# XD-02 Red Dwarf Mines, L4: notes

A new dungeon built from the written brief (L1 to L3 here, `devdocs/xeen/MAPS.md` row XD-02, QUESTS.md Story M3,
MONSTERS_AND_ITEMS.md) with the Map Studio, by one agent, 2026-11-13, after XD-01's two passes. No original exists;
nothing was measured from a shipped map except scale, light and dressing (below).

**After the third pass** (section "Third pass: the user's walk" at the end): the user's six points of his walk
through the second pass fixed; 0 faces in one plane; playtest 191 steps four of four on the tenth merge's binary;
installed in `output/studio_play/xeen_root`. **After the second pass** (section "Second pass: the user's lessons"):
main rooms at the shipped median (upper quarter 1.80 M), 0 faces in one plane (54 before). The paragraphs below are
the first pass's.

State: `oymap validate` no issues, `fmt --check` clean; the build's five warnings are all placed monsters' names
(`Tallymaster`, `Tiger Mole`, gap 9). 43 rooms, 43 sectors; 37 reached on foot, the other six by design (three bunk
shelves 160 high, three ore chutes 384 up a wall). The playtest (171 steps) passes four runs of four
(`output/studio_cal/xd02/run/four.out`, logs `final_1.log` to `final_4.log`).

Scratch: `output/studio_cal/xd02/` (`go.sh` builds, installs into `mount/` and plays one test; `four.sh` the four
runs; `tour.yml` takes the pictures from the scratch root `root/`; `ref/` the shipped mines; `repro/`; `look1`-`look4/`
the earlier takes). Pictures: `output/studio_cal/xd02/shots/` (35 in the game, HUD off, `captions.yml`, `plan.png`,
`iso.png`).

**What was scripted.** The first shell and objects were written by two generators in my scratch folder,
`output/studio_cal/xd02/tools/gen_rooms.py` and `gen_objects.py` (geometry helpers `geom.py`): they compute the stope's
bench trapezoids from its sixteen-sided outline, the trestle's deck plane and bents, timber sets, rails, carts built of
blocks, and they hold every room, object and event. They were rerun after each change during the work; the project
files are now the source (no hand edit has been made that a rerun would lose, but none should be rerun blindly).

## Shipped mines looked at first

`output/studio_cal/xd02/ref/`: MM7's own Red Dwarf Mines `7d34` (plan, iso, 11 game pictures, metrics), MM6's
Snergle's Iron Mines `6d09` (7 pictures), and the renders and metrics of MM7's Nighon Tunnels `7d35` and MM6's
Dragoons' Caverns `6d06`. What they taught, nothing of theirs copied:

- `7d34` is winding tunnels between dark caverns; the timbering is only at passage mouths (heavy frames with a pair of
  torches), the caverns themselves are near black and lit in pools at the frames; c2b red rock, cfb1 floor; 4.95
  light sources per M units², 2.6 decorations per M; monsters stand in packs in the caverns, not in the tunnels.
- `6d09` is a dwarves' hall map: dressed stone under beamed plank ceilings, barrels, dwarves standing in groups of three
  or four; 1.03 light sources per M, 59 sectors, 40.6 M units².
- `7d35` is 216 M units² of cwb1 tunnels with no doors; `6d06` 59 M, 70 sectors, 35 doors.
So: timber at mouths and in sets along drifts, lamps in pools with dark between, dwarves' rooms in dressed stone with
plank ceilings on beams, monsters in packs where there is room to fight.

## The world it is built in

As XD-01: `world: xeen` validates but render, solve and the game refuse it, so L4 says `world: mm7` (one line).

| Brief | Built as | Why |
|---|---|---|
| Slot 1 Mad Dwarves (Mad Dwarf 7) | MM7 Dwarf family, slot tier 1 (Dwarven Soldier, level 10, 40 hp, 4D2+4) | The only hostile-looking dwarf with a 3D model in MM7; no level-7 dwarf exists. MM7 makes Dwarves the party's ally: a load event makes the three Dwarf rows hostile (gap 1) |
| Slot 2 Spiders (5 / 10) | Spider family, tier 2 (Giant Spider 5, Venomous Spider 8, Widowmaker 12) | The same family; spawns that the brief puts at level 5 say `tier: a` |
| Slot 3 Bats (Giant Bat 3 / Bat Queen 10) | Bat family, tier 1 (Giant Bat 3, Vampire Bat 6, Inferno Bat 9) | The same family |
| Tiger Moles (Burrower 9) | Troglodyte Drone (412, level 9), placed, named "Tiger Mole" | A level-9 cave burrower with a 3D model |
| Tallymaster (Mad Dwarf 10, doubled hit points) | Dwarven Soldier with `hp: 80`, `name: Tallymaster`, `immobile` | The game ignores `hp` (XD-01 gap) and shows the name only on the corpse |
| The cocoon's level-10 spiders | Venomous Spiders (401, level 8), placed, group 4 | |
| brake_key 12011 | Key 2111 | Xeen items are unregistered |
| qbits 110020-110021 | kept | The game sets and reads them (the playtest checks both) |
| The pools' "once per character" | player bits 11021-11024 (provisional) | No word for a player bit (gap 3) |
| music `cave` | MM7 track 18 | The game refuses a name |
| X1, X4, XD-03 | Emerald Island `7out01.odm` at XD-01's arrival point | None exists |

With a real Xeen world: `world: xeen`; the slots to Mad Dwarf 7, Spider 5/10, Giant Bat 3/Bat Queen 10 and the moles
to a Tiger Mole row (the load event that makes the clan hostile goes, the Tallymaster's numbers come from a Mad Dwarf
row), the key to 12011, music by name, the three neighbours to X1, X4 and XD-03 (with their arrival points), sounds
from the Xeen audio folder. The textures are the shared MM6-MM8 library and stay.

## What the brief asks, and how each thing was built

Shell (L3's plan and coordinates kept wherever they worked; departures below):

- **Adit mouth and haul drift.** The portal is the east wall: the exit face shows sky (`sky_clo1`) under a lintel on
  two posts; three timber sets (dark posts against both walls, a cap beam) under plank lagging; rails from the
  party's feet; a tipped ore cart (blocks) by the north wall; the clan's skull warning (`warnsign`, a clicked panel:
  "MAD DWARF CLAN. DIG ELSEWHERE."). The drift is one climbing path room (L3's drift and incline) with timber sets
  every 360 and the first fight (bats) round its bend.
- **Top Station.** Rock hall under a plank roof on three cap beams, the timber loading platform (32) along the west
  wall with the trestle gate in it (sill 32, level with the platform and the car's deck), lantern, brazier, barrels,
  sacks. Plank doors to the lamp room and the foot drift.
- **Lamp room** (wedge): a lamp rack (a shelf on posts) with five unlit lamps over it, the chest under it, a Torch Light
  scroll on the rack. **Sorting floor**: two sorting tables, two lanterns hung from beams over them, the three black
  chute mouths 384 up the north wall (rooms, bats roost in the middle one), spilled ore, a gold vein in the slanted
  west wall, the chalk mark (a clicked panel) over the dry-stone wall that sinks (a secret door) into the **forgotten
  strongroom** (dressed stone, a fallen stool, an empty pay rack, the payroll chest).
- **The chasm and the trestle.** The chasm is a box 2368 deep, unlit, a ragged roof by points. The trestle is five
  bents of two dark legs, a cap, a lower tie and X braces (raking beams), carrying a plank deck that rises 272 from the
  Turntable's gate to the Station's (a hanging sloped slab, `thickness`), with hand rails on both sides. **The car is a
  mover that carries the party** (`mover:trestle_car`: a plank flatcar with sides and iron wheels as parts; 1584 west and
  224 down in ten seconds). Gates (sliding doors) at both ends are down where the car stands and up where it is away,
  so nobody steps into the chasm; the car itself, a lever on the loading platform and a lever at the Turntable's gate
  send or call it. It runs only while the points are set for the trestle.
- **Foot drift**: the old walking way round the chasm (path, incline, bend) with rotten props (`d6ebeam`), a lamp at
  each end, the ragged window (sill 64) down onto the trestle. **The rockfall** is a plate under the rotten props and
  a mover of rubble hidden in the roof that crashes onto the drift's north half once (7 damage to the party, a camera
  shake) and stays as a heap to walk round.
- **The Turntable**: sixteen-sided cavern under an uneven roof (512 at the walls, 736 at the crown), the timber disc on
  its iron ring with rails to the trestle gate and the east line's gate, the points lever on a post beside it, two
  braziers, four lanterns, green signal lamps over the two gates (switched lights) that show which line is live.
- **East line and the flooded working.** The east line is one straight drowned rail tunnel 2260 long, black water 40
  under the gate sills with the rails just showing, lamps at its head and half way. **The east cart is a mover that
  carries the party on a level slide** (1960 south-east in twelve seconds; the build gives every mover `carry`); gates at
  both ends as on the trestle; it runs only while the points are set east; levers at both ends call it. The buffer
  landing at its end falls 256 by uneven floor to the **flooded working**: an irregular low cave (roof by points, rough
  walls), its floor the world's moving water (marked water), plank walkways on trestles, two rock islands, a vein, two
  tiger moles standing in the water; the **dry hump** is a rock shelf one step up with the gold pool sunk in it.
- **The camp.** Mess hall (L3's L): dressed stone over a block footing, plank ceiling on beams, two rock pillars, two
  long tables with benches, bowls, plates and goblets on them, the cold hearth with its pot in the angle of the L, two
  braziers. Bunk cut with three bunk shelves (unentered, 160 high) and two footlockers. Tally steps (three treads) and
  the iron-banded door into the **tally room**: bronze tally plaques on four walls, the tallymaster at his candle-lit
  table, three guards, the clan's strongbox with the brake key.
- **Chapel**: octagon of dwarf blocks, eight dressed pillars, a stone lantern (a raised ceiling level) over the green
  pool, which is sunk 32 behind a kerb, its water a clicked surface; the tablet is a bronze plaque on a plinth facing
  the door; two braziers; smashed carvings (rocks). Carved stone double doors two steps above it.
- **West line**: the derailed rail tunnel rising west (a lying cart, rotten props, a guttering lamp), the landing with
  the first ventilation door and the repair niche (a cart up on blocks, the wheelwright's bench and axe), the upper
  incline, the second ventilation door, and the **collapsed west adit**: the fall is a mover (rock to the roof with two
  boulders and braced props as parts) in front of the X4 exit face; **the winch** (a clicked drum on a frame) sends it
  down the old ore chute under the floor once, with a roar (camera shake), sets `x4_adit_open` and lights the daylight
  at the far end; the exit then works.
- **The Open Stope.** One sixteen-sided pit room 2240 across, floor -1152, a ragged roof by points about 1600 up, deep
  rock to 640 and red rock above (a band). **The spiral is inside it**: ten rock benches 320 wide against the walls
  (platforms; ramps by `top_heights` per corner), 0.6 of a turn clockwise from the rim ledge (-384, ENE) round the east,
  south and west to the floor (WNW): five level ledges (-384, -544, -704, -864, -1024) and five ramps (160 or 128 down over
  437), all open to the pit behind a timber rail (raking beams) on posts. A lantern hangs at each ledge, the ramps
  between are dark. The floor has two spoil heaps (sloped blocks), two abandoned carts, two lanterns on props. The
  **rim** is a room behind the pit's north-east wall, open over its whole east-north-east wall onto the first ledge
  (the reveal) after the **low gallery** (a rock tunnel with a cross-section, square ends at both mouths).
- **The hoist** is a mover cage (iron frame and rails as parts) at the floor's north-east wall, riding 768 to the rim's
  hoist gate (an iron grille door, up only while the cage is at the rim), under a head frame of beams with the cable
  hanging to the floor. Ridden once, it can be called from the rim and from the floor (`hoist_used`).
- **Red pool grotto** off the floor's north side, one step down, rough walls, the red pool sunk in its point (lava-shader
  surface without the lava flag, red glow). **The rich vein** is in the floor's north-north-east wall; mining it opens
  the rock beside it (a door with the wall's own rock) on a burrow where two tiger moles wait.
- **Spider galleries** through a low crawl (a 572-long path room) off the south-south-west ledge: rough walls, an uneven
  roof, two rock islands splitting it into three workings, spiders, bones, cave fungus glowing faintly, the cocooned
  miner (a hanging corpse with his web-wrapped pack, a chest) guarded by three Venomous Spiders; the straight west wall
  is the web wall (a secret door with the web picture) to the **blue grotto**, whose floor is nearly all a shallow blue
  pool among crystals.
- **Deep Line station**: down a 960-long rock-cut ramp from the floor; rails west to a buffer stop, the chained cart
  (blocks) on them, a chain (a mover) dropping into the rail bed when the brake key is used on the brake wheel, two
  lanterns, and the Deep Line's mouth: a cutting dropping 192 west into the dark, whose far end is the exit.

Surfaces (pass 1, replaced by the texture pass below): 37 textures. cwb1 red rock 34 % of faces, c2b deep rock 20 %, red dirt and earth floors, dark timber
(`beamplnv`, `beamplnh`, `d6ebeam`), plank lagging (`bmplnk`), dressed stone and dwarf blocks for the camp and chapel,
iron for rails, wheels and the hoist, gold seams (`cwb1gold`, `c1gold`) that go dull once mined (the switches' `on`
texture). Pools: green slime liquid, gold ore picture, lava shader for red, blue water liquid.

Objects and wiring (every mechanism a preset with conditions and effects; Lua only where marked):

| Brief | Built |
|---|---|
| Entrance and X1 exit | `start` inside the portal facing west; `exit:x1` on the portal (sky) |
| Trestle cart ride | `mover:trestle_car`; three switch events (the car, two levers) `toggles` the car and both gates, `condition: not map_var turntable_east` |
| East cart ride | `mover:east_cart`, three events the same way with `condition: map_var turntable_east` |
| Turntable puzzle | `evt:points` script preset: condition `turntable_east` → set 0, east lamp off, trestle lamp on; `else_effects` the reverse |
| Hoist | `mover:hoist` + `door:hoist_gate`; the cage's own event sets `hoist_used`; bell-pulls at the rim and the floor need it |
| Rockfall trap | `plate:rockfall`, step, once, opens `mover:rubble`, 7 damage, camera shake (Lua) |
| Winch | clicked platform, switch preset, once, opens `mover:fall`, `qbit x4_adit_open`, daylight on, camera shake (Lua) |
| X4 exit | `exit:x4`, condition `qbit x4_adit_open` |
| Brake key, Deep Line | strongbox chest with the key; the brake wheel switch, condition `item brake_key consume`, once, opens the chain, sets `deep_line_unchained`; `exit:deep` with that condition |
| Four pools, +2 once per character | script presets on the water platforms: condition `lua: not IsPlayerBitSet(PlayerBit(n))`, effects `add BaseMight/BaseEndurance/BaseAccuracy/BaseIntellect 2` and `lua: SetPlayerBit`, else "The water tastes of nothing." |
| Six gold veins | switches with `off` gold rock and `on` plain rock, once, gold 80-200, their glint light off; the rich one opens the burrow (`door:mole_rock`) and shakes the camera (Lua) |
| Tablet | clicked plaque, `message` with the four colours and "THE BLUE SLEEPS BEHIND THE SILK" |
| Secret walls | strongroom (sinks) and web wall (rises), `secret: true`, door presets, `action: open` |
| Doors | lamp room, foot drift (plank, hinged), bunk and tally (iron-banded), two ventilation doors (grilled), chapel (two folding leaves) |
| Chests | footlockers (level 1, 2 and 1 random), lamp room (1, 2), strongbox (2, 2 random, 150 gold, the key), payroll (3, 3 random, 400 gold, an amethyst), the cocoon (2, 2) |
| The clan hostile | a load event, `lua: evt.SetMonsterRelation(229/230/231, 0, 4)` (gap 1) |
| Lights | 30 iron lanterns, 7 braziers, 2 hung lanterns, a candlestick; 37 point lights, 27 of them pulsing (the four pools, six gold glints, five ledge lanterns, fungus, swaying lamps) and two switched signal lamps plus the switched daylight |
| Population | 22 monster spawn points (10 dwarf, 7 spider, 5 bat) where the brief puts them; 11 placed (tallymaster and three guards, two moles in the water, two in the burrow, three cocoon spiders); 2 item spawns |
| Floor items | Torch Light scroll on the lamp rack, the wheelwright's axe, a ruby chip by the rich vein, a potion by the cocoon, a bottle on the mess table |

## Scale against the bands

`oymap metrics <L4> --reach` (`output/studio_cal/xd02/metrics.json`); bands from
`devdocs/xeen/research/MAP_CRAFT_CALIBRATION.md` 3.1, 3.3 and 6.3 (CALIBRATION.md itself names no numbers).

| Figure | XD-02 L4 | Band |
|---|---|---|
| Floor area | 37.7 M units² (walkable 28.5) | M 40-70; MM7 canon 24 / 73 / 90. The brief's own L3 measured 33.5 |
| Sectors | 43 | M 20-35, L 35-55; mid median 31 (the chutes, bunks, steps and grottoes are small sectors) |
| Floor levels | walked 256 to -1216 in seven bands (west adit 256, adit 0, station -192, Turntable and camp -384, flood -640, galleries -864, stope floor and Deep Line -1152 / -1216) | 2-4; height range MM7 1,050 / 1,800 / 2,860, here 1,472 walked |
| Loops | 2 (the chasm: car and foot drift; the stope: spiral and hoist) | at least 1 for M |
| Doors | 15 doors and 6 movers (22 door records); 22 door events | M 8-16 doors, 5-14 door events (the rides add six) |
| Monsters | about 69 (22 markers of 2-4, 11 placed): 1.6 per sector | M 35-65; brief about 65 |
| Chests | 6 (with the cocoon) | 3-7 |
| Secret faces | 4 (two secret doors) | 1-6 per M dungeon |
| Plates, traps | 1 plate, 1 trap event | 1-15 plates; traps on 1 map in 3 |
| Boss | the Tallymaster (named, hp 80 ignored) | about 1 dungeon in 5 |
| Light sources | 77 (40 on decorations, 37 point lights); metrics counts 50 (pulsing lights are not records): 1.33, really 2.0 per M units² | 7d34 4.95, 6d09 1.03, XD-01 1.85; brief 45 |
| Decorations | 116, 3.1 per M | 7d34 2.6, 6d09 1.55 |
| Doorways | median 256 wide, 320 high | 256 x 256 |
| Sector height | median 482 (192 bunks to 2368 chasm) | 464-592 mid rooms; at least 384 on foot |
| Non-orthogonal rooms | 21 of 43 (49 %); 16 with sloped, uneven or vaulted floors or roofs | at least 40 %, 25 % |
| Main wall texture | after the texture pass t3ll6 19 % of faces (walls: t3ll5 28 %, t3ll6 26 %, crstont 24 %); pass 1 cwb1 34 %, c2b 20 % | one texture 45-85 % |
| Clickable faces | 289 | 50-170 (the pools' water surfaces and the gate doors count every face) |

## Order of play (`oymap solve`, `output/studio_cal/xd02/solve.txt`)

```
step 0: 7 sectors  the adit, the drift, the Top Station, the sorting floor
step 1: 21 sectors the lamp room and foot drift doors, the strongroom's wall, the trestle car (car and both gates)
                   -> the foot drift, the chasm, the Turntable and everything open off it
step 2: 8 sectors  bunk, chapel, tally and first ventilation doors, the hoist, the east cart (after the points)...
step 3: 1 sector   needs item 2111 (the brake key, from the tally room's strongbox): the brake -> the Deep Line exit
step 4: the winch  -> the X4 exit
never reached: the three bunk shelves and the three chutes (by design)
```

That is the brief's order: adit, drift, Top Station, the trestle (or the foot drift) to the Turntable, the camp and the
key, the rim, the spiral and the stope, the Deep Line; the west adit is an optional branch off the Turntable.

## Playtest (`playtest.yml`)

171 steps, passes four runs of four (`run/four.out`). A level-6 party walks in by the adit and reads the warning, takes
the lamp rack's scroll, chips the sorting floor's vein (pays 120, then nothing), reads the chalk mark, sinks the wall
and loots the payroll chest (its fixed amethyst); rides the car over the chasm, walks back by the foot drift (the
rockfall comes down once behind it), calls the car with the station's lever and rides it again; sets the points east
(the trestle car now refuses), rides the east cart down the drowned line, crosses the planks, chips the flood's vein,
drinks the gold pool twice (Accuracy once, then "tastes of nothing"), rides back and resets the points; opens the
tally door, kills the guards and loots the brake key; opens the bunk door; reads the tablet and drinks the green pool
twice; opens both ventilation doors, finds the X4 exit shut, works the winch (the fall goes, `x4_adit_open`) and walks
where the fall stood; goes through the gallery to the rim, chips its vein, walks the spiral down ledge by ledge, chips
the south-east ramp's vein, crawls into the galleries, cuts the web wall and drinks the blue pool twice, chips the
south-west ramp's vein, comes down to the floor, drinks the red pool (the drinker's Might +2 exactly, and not again),
mines the rich vein (200 gold, the burrow opens, a mole comes out, the moles are killed), picks up the ruby, rides the
hoist up, sends it down and brings it back with the rim's bell-pull, rides it down, finds the Deep Line chained, uses
the key (taken by the brake, `deep_line_unchained`) and leaves down the Deep Line to the stand-in map with both bits
and its loot.

Nothing depends on chance: only the payroll chest and the strongbox are looted (their fixed items checked), the plain
doors are opened with `open_door` (a dwarf may have opened one first), and every walk clears hostiles with a radius
kept small near the burrow and the tally room (clear_hostiles kills through floors and walls). The burrow's moles are
checked after the rock opens, not before: in one trial run a mole in the closed burrow died during an unrelated walk
far away, which I could not explain (`run/molecheck2.log`, step 206).

## Departures from the brief

1. **The spiral is inside the Open Stope**, as rock benches against its walls, not ten rooms stepping round its outside.
   L3's own note says it stepped outward only because rooms could not lie in one another; the brief's picture is a
   funnel with a spiral of ramps and railed ledges. All five ledges and all five ramps are railed and open to the pit
   (L3: four ledges, rock-cut ramps); the spiral's foot is the floor itself, so L3's landing room is gone.
2. **The carts are real rides**: movers that carry the party, not scripted moves. Gates (doors) bar each line while its
   car is away, which L3's 96 sills did for walkers.
3. **The east line is one straight drowned tunnel at the Turntable's level** with a buffer landing that falls 256 to the
   flooded working (L3: an incline and a drowned stretch bending south). A mover runs in a straight line in one room.
4. **The flooded working's north edge moved south 320 and its east wall made upright**, for the landing and the dry
   hump; the hump is its own small room with the gold pool sunk in it (a pool cannot be sunk into a raised level).
5. **The pools are sunk 32 in their floors** with a clicked water surface (L3: brim-full basins).
6. **The rich vein's moles wait in a burrow behind a rock door**, not hidden actors (no word: gap 2).
7. The adit mouth is level; its 64 fall is in the haul drift, which is one climbing path with L3's incline.
8. The Deep Line has a mouth room; the deep ramp is 960 long (the landing it started from is gone); the crawl is 572
   long because the galleries stay where L3 put them.
9. The collapsed adit is 1024 long and 448 wide, east-west, so the fall fills its west end in front of the X4 face.
10. The chapel's double door is two folding sliding leaves (a hinged door has one leaf).
11. **Six gold veins** (the brief counts six and lists seven places; the floor's south vein is dropped: the spiral
    covers that wall). Values 80-200, 710 in all (the brief: about 600).
12. **More light**: 77 light sources against the brief's 45, and the chasm has a lamp on the trestle's middle bent and
    lanterns at both car stops. In the first pictures the stope, the chasm and the galleries were black; the spiral's
    ramps stay dark between lit ledges.
13. The Tallymaster is `immobile` behind his table (a guard at his post); 43 rooms instead of L3's 50.

## Gaps (what I wanted to say and could not), most harmful first

1. **A map's own monster relations, or a slot's hostility.** MM7's Dwarf family is the party's ally in `hostile.txt`, so
   every spawned clan dwarf stood peaceful (27 dwarves, 4 hostile: the placed ones). The load event's Lua
   `evt.SetMonsterRelation(229|230|231, 0, 4)` fixes it. The game has `SetLocalFactionRelations` for a map's own
   cells, but no studio word reaches it: `project.yml relations: [{faction, other, relation}]` or
   `map_stats.slots[].hostile: true` would. Repro `output/studio_cal/xd02/repro/clan_peaceful/` (a copy of L4 without
   the event; `run.log`: "found 4 living actors of monster 229" hostile).
2. **A placed monster hidden until an event** (the plan's `hidden_until`): the rich vein's moles live in a burrow room
   behind a door instead. `monsters[].hidden: true` with an effect `show_monsters: <group>` (outdoor has
   `show_actors`) would say it.
3. **Once per character**: no condition or effect for a player bit; the pools use Lua (`IsPlayerBitSet`,
   `SetPlayerBit`). A condition `player_bit: n` and effect `set_player_bit: n` (or `uses: {per: character}`) would.
4. **Camera shake** (the rockfall, the winch, the rich vein): Lua `evt.CameraShake`. An effect `shake: {intensity,
   seconds}`.
5. **No rotating mover**: the turntable cannot turn; the points are shown by two switched lamps. `movers[].rotate`
   (about a point, degrees).
6. **A map exit only on a wall face**: the Deep Line's cart cannot be the exit; the party clicks the dark face beyond
   the buffer stop. `exits[]` on a platform or a mover, or an effect `exit: <neighbour>` for any event.
7. **Things riding a mover**: the trestle car cannot carry its lantern or a decoration (only blocks, chests and
   switches ride). `lights[].rides`, `decorations[].rides`.
8. **Placed sounds** are still refused for an MM7 project (no drip, wind in the chasm, creaking cable):
   "objects.yml: sounds[0].sound: the world mm7 has no sound file waterdrip.wav". Repro `repro/sound_mm7/` (XD-01's).
9. **Placed monsters' names** show only on corpses (Tallymaster, Tiger Mole) and their `hp` is ignored (XD-01).
10. **An opening's reveal**: a secret door in a timbered room shows the room's timber frame round it; the strongroom's
    and the burrow's openings had to be drawn from the plain room's side. `openings[].reveal` would say it.
11. **A sunken level cannot be clicked**: a pool's click source has to be a platform lying in it as its water.
    `levels[].id` as a click source.
12. No mine-cart, winch, brake-wheel or hoist-sheave models: all are blocks, which read, but plainly.
13. Arrival points for the other entrances (from X4, from XD-03) cannot be said in this project; only one `start`.

## Tool defects (repros under `output/studio_cal/xd02/repro/`)

1. **`consume` inside `any` is dropped without a word.** `condition: {any: [{qbit: freed}, {item: key, consume:
   true}]}` builds `if not ((IsQBitSet(...)) or (HasItem(2111))) then ... end` and never `RemoveItem`; validate and
   build say nothing. Found when the brake kept the key. Repro `repro/consume_in_any/` (`build/repro_any.lua` lines
   5-13; `oymap build repro/consume_in_any --assets assets_dev --out <dir>`).
2. **`once` on a click `script` preset is dropped without a word**: no once variable, the handler runs every click
   (the schema says once is for switch presets and step, timer and load events, but the build should warn). Same repro,
   `evt:winch` (lines 15-18). Found on the winch, which is now a switch preset.
3. **The movers' schema text is stale**: "a mover whose travel is level slides away under the party's feet (the engine
   carries only on movers that rise or sink)", but the build writes `carry: true` on every mover and the east cart's
   level slide carries the party (playtest, the east cart steps).
4. Test harness: `clear_hostiles` (and `walk_to`'s) kills through floors and walls by plan distance: a walk on the west
   line killed the moles in the burrow 1000 below it, and walks in the mess hall killed the tally guards (XD-01 saw the
   same). A burrow mole once died with no kill near it (`run/molecheck2.log`); not explained.
5. Minor: `plan.yml level` takes only L0-L3, so an L4 plan says `level: L3`.

## What in the brief was unclear

- The gold veins: six counted, seven places named.
- One waiting cart that "turns with the turntable" against "a cart at each gate" (mechanisms); with movers each line
  needs its own car, so the turntable only decides which line runs.
- Whether the trestle may be walked: "the trestle has sides" and "both ends are gates that walkers cannot pass". Built:
  a railed deck the party can step down onto from a car, gates that bar it while the car is away.
- Mad Dwarf 7 and the Tallymaster at 10 have no rows; the nearest dwarf is level 10, so the camp is harder than the
  brief's band (packs of three level-10 dwarves for a level 5-8 party).
- "Returning carts arrive here" and the X4 entrance: where those arrivals stand belongs to the other maps.
- The chasm is "unlit" and the stope floor "lit only from the ledges": as pictures both read black; I added a few lamps.

## Pictures

Best: `shots/05-trestle-car-waiting.png` (the car in the gate, the trestle running out into the dark),
`shots/25-rim-reveal.png` (the pit and its railed spiral from the rim ledge), `shots/13-turntable-points.png` (both carts
in their gates, the live line's green lamp), `shots/23-west-adit-cleared.png` with `22-west-adit-fall.png` (before and
after the winch), `shots/19-chapel.png`. Also good: `06-trestle-car-coming.png`, `18-tally-room.png`,
`29-hoist-at-rim.png`. Weakest: `shots/28-stope-floor-benches.png` (from below the stope does not read as the big
funnel: the benches are blocky tiers in the dark) and `shots/21-west-line.png` (a long plain tunnel; the derailed cart
does not read).

Fixed after looking: the first take's stope, chasm, east line and galleries were black (ambient lowered, ledge,
floor, line and fungus lights added); cap beams showed rock (beams took the wall texture: given timber); the ceiling
lagging was too pale (darker planks); a campfire stood on the tally table (`7dec02` is a fire: now the candlestick
`dec02`); the sorting floor's lanterns floated (hung from two beams); the tablet's rune band was stretched into
stripes (a bronze plaque on a plinth); the gold and red pools drew as plain blue water (gold ore picture, lava shader);
the burrow's and the strongroom's secret doors showed a timber frame (drawn from the plain side); the cart at the rail
head stood in the arrival view (tipped against the north wall); the mess hall and turntable views were blocked by
pillars and dwarves (camera places). The secret doors' red pulse in pictures 09 and 33 is the game's Perception
highlight, not a fault.

## Judgement

As a dungeon it has what the brief promises and they all work: two real cart rides (the trestle car is the best moment:
step onto the car on the loading platform and roll down over the black chasm to the Turntable's lamps), a loop round
the chasm with a trap in it, a points lever that decides which line runs, the hoist that closes the stope's loop, four
pools that each strengthen a character once, six veins that go dull, two secret walls with clues, a winch that opens a
second way out, a key fought for in the tally room. The stope's spiral, read from the rim, is the brief's funnel: ledges
with rails and lanterns stepping down round the pit to a floor of spoil heaps and abandoned carts. The chapel, the tally
room and the timbered upper workings look like places.

Its weaknesses: one rock texture (cwb1) carries a third of the map and reads busy and grey-pink under bright light; the
caves (galleries, flood, grottoes) are plain dark shells with a few props; from below, the stope is a dark drum of
blocky tiers, not a cathedral; the carts and the winch are boxes; there are no sounds; the turntable does not turn. The
clan are MM7's friendly dwarves made hostile by a line of Lua, at level 10 in packs, which is harder than the brief's
band for a level 5-8 party, and the long walk to the west adit has little in it. A player would enjoy the rides and the
stope; the rest is a sound, well-wired MM7-style mine that wants a second pass on materials (a darker second rock for
the caves, timber dressing in the stope, a real cart model), sounds when the word reaches MM7, and a Mad Dwarf row.

## Texture pass (2026-11-13, a second session)

Why: the user's look at XD-01 ("avoid making it a Frankenstein's monster"; ship windows in a warehouse) and
REBUILD_PROCEDURE.md's "Textures for a new dungeon". Pass 1 had picked 36 textures one by one from 23 shipped maps, 10
of them from no shipped dungeon (the ship woods `bwooda2` with its grilles and `bwoodb1`, the outdoor planks `bembllg`,
`tdoora`, two irons, `7trim9_32`, ...), and one busy red rock (`cwb1`) on 45 % of all wall area. Shape, objects, wiring
and the playtest are unchanged; only surfaces moved. Pass 1 as it stood: `output/studio_cal/xd02/pass1_backup/`.

### Shipped places looked at

`texture_use.py --map` and the game (`output/studio_cal/xd02/texpass/ref/`: tours of 6d05, 7d07 and d41 beside the
earlier 6d09 and 7d34 ones in `ref/`; contact sheets of each set, `texpass/sheet_*.png`):

- MM6 Snergle's Caverns `6d05`: the dwarves' mine. Tunnels of dark grained rock (`t3ll6`, walls and roofs) with plank
  doors, barrack rooms of red rock (`t3ll5`) under beamed plank ceilings (`d2ceil1`, `d2ceil2`), caverns of blue-grey
  and pale stone (`crstont`, `crflr3`, `crwl3`) under gravel (`crdrf1`), floors of red earth (`t3oor1`) and dark rock
  (`d2ceil4`), dark posts and beams (`t3d2abs`, `t3d2abe`), its own door (`t3dr1`) and water (`6wtrtyl`).
- MM6 Snergle's Iron Mines `6d09`: the same dwarves' halls. Dwarf blocks under a carved frieze (`d7wl1ctr`),
  rough-dressed stone under a dressed course (`d7wl2ctr`), dressed blocks (`d7trim8`), rune tiles (`d7flor4`), carved
  ceilings (`d7ceil2`), carved doors (`d7dor1`-`d7dor3`), furniture wood (`cbedsqr`), the shipped chest set (`ch1*`).
- MM7 The Red Dwarf Mines `7d34`: one rock (`c2b`) and one floor (`cfb1`) lit red, timber frames; its own gold seam
  (`c1gold`, which is `c2b` with gold), iron sheet (`ch004i`) and bedding (`t2bedsht`).
- Not taken: Thunderfist Mountain `7d07` (`c2b` nearly everywhere, near black in the game); MM8's Dark Dwarf Compound
  `d41` (grey and black stone under plank ceilings: a good dwarf set, but grey, and a fourth source; its `gn_mtl02` iron
  was the alternative to `ch004i`); Stone City `7d24` (built on `cwb1`, the texture this pass removes).

### Families chosen, per area

1. **The workings, the caves and the camp: Snergle's Caverns `6d05`** (38 of 43 rooms). A dwarves' mine whose set has
   the different rocks a mine shows by their job, and whose rooms in the game look like the ones this map needs. Used
   the way 6d05 uses them:
   - worked face `t3ll5` (red): the timbered chambers (adit mouth, Top Station, lamp room, east landing, west line
     landing, repair niche), the red workings (sorting floor, chutes, Turntable, stope rim), the camp (mess hall, bunk
     cut, bunks) and the spiral's bench faces;
   - raw face `t3ll6` (dark, grained): the timbered drifts (haul drift, foot drift, incline and bend, west line and its
     upper incline, collapsed adit), the untimbered tunnels (gallery, crawl, deep ramp, Deep Line station and mouth), the
     drowned east line, the Open Stope's pit faces (pass 1's band of deep rock is gone: one face), and the roofs of the
     red workings;
   - natural rock `crstont` (blue-grey): what the miners broke into: the chasm, the spider galleries, the grottoes, the
     dry hump, the flooded working, the burrow;
   - floors `t3oor1` (worked) and `d2ceil4` (caves, pit, deep line); gravel `crdrf1` on cave roofs and as spoil heaps,
     spilled ore, cart loads and the rockfall's top; lagging `d2ceil1` (timbered rooms and drifts, the trestle's deck,
     where its dark gaps read as open sleepers) and `d2ceil2` (the camp's ceiling, plank tops of tables, benches, the
     loading dock, walkways, car decks, the turntable disc, the hoist floor); posts, legs, props and lever plates
     `t3d2abs`, cap beams, stringers, rails of the spiral and plank edges `t3d2abe`; plank doors `t3dr1`; water `6wtrtyl`.
   The camp is not a third family: 6d05's own barrack rooms are red rock under a beamed plank ceiling (its shots s9,
   s29), which is what a clan camp in old workings is; `d2ceil2` overhead sets it off from the drifts' `d2ceil1`.
2. **The Red Dwarves' worked rooms: Snergle's Iron Mines `6d09`** (chapel and its steps, tally room and its steps, the
   forgotten strongroom). The same dwarves' halls as the mine above, so the two families are one place: its mine and
   its halls. Chapel `d7wl1ctr` walls, `d7trim8` pillars, kerb, plinth and jambs, `d7flor4`, `d7ceil2`, `d7dor1` (one
   picture across both folding leaves); tally rooms `d7wl2ctr`, `d7flor4`, `d7ceil2`, `d7trim8` jambs and risers,
   `cbedsqr` table, `d7dor3` (6d09's single plank door with its carved skull: the tally door is one hinged leaf, and
   6d09's double-door pictures would swing as one); strongroom `d7trim8`, `d7flor4`, `mnwl2` roof. The mess hall's
   hearth is `d7trim8` too (dwarf masonry in the camp).
3. **Three things neither Snergle map has, from MM7's own Red Dwarf Mines `7d34`:** the gold seam `c1gold` (the six
   veins; mined, each shows its wall's own rock), iron `ch004i` (rails, buffer stops, wheels, the hoist cage, the
   chain, the brake wheel, the points lever, the winch drum's ends) and bedding `t2bedsht` (the bunks' pallets).
   Chests: the shipped chest set `ch1frntb` (front), `ch1side` (ends), `ch1topb` (lid), all stretched once, as 6d09's and
   6d05's own chests; the cocoon keeps its web.

How each kind of thing reads now (pictures `shots2/`, close-ups `texpass/look2/`): plank doors with 6d05's bronze
roundel; the chapel's carved double door and the tally room's skull door from 6d09; the four line gates and the hoist
gate as slatted timber (`d2ceil1` stretched: the hoist gate reads as a barred gate in the dark); the strongroom's
secret door as dry-stone blocks (`d7trim8`, laid at size) walled into the sorting floor's red rock under the chalk mark,
invisible from inside the strongroom; the burrow's rock door as the pit face; the cars as plank decks on dark stringers
with grey iron-banded side boards (`ch1topb` stretched) and iron wheels; the ore carts as grey iron-banded plank boxes
with gravel loads; the hoist as a bright iron cage with a plank floor; the winch as a dark timber drum with iron ends;
the fall and the rockfall in their tunnels' own rock.

### Before and after (`texture_use.py --project`)

| | Pass 1 | Texture pass |
|---|---|---|
| Textures | 36 | 36 |
| Main source maps (the tool names each texture's most-used map) | 23 | 18 |
| Textures in the chosen families (6d05 13, 6d09 12, 7d34 3; `ch1side` is in both Snergle maps) | 6 (all 7d34: `c2b`, `cfb1`, `7trimd`, `7trimda`, `7wtrtyl`, `c1gold`) | 27 |
| From other shipped dungeons | 20 | 6 (`7slimywtr`, `lavatyl`, `orertlga`, `sign22`, `sign128`, `sky_clo1`) |
| From no shipped dungeon | 10 | 3 (`warnsign`, `runeeyvlij`, `web32n735s`) |
| Largest wall texture (area of upright faces) | `cwb1` 45 %, `c2b` 28 % | `t3ll5` 28 %, `t3ll6` 26 %, `crstont` 24 % |
| Largest texture, all faces (`oymap metrics` palette) | `cwb1` 34 % | `t3ll6` 19 % |

The "main source maps" figure undersells the change: `d2ceil1` counts for Icewind Keep, `t3ll5` for the Temple of
Tsantsa, `d7flor4` for the Lair of the Wolf, because those use them most; all are 6d05's or 6d09's own
(`output/studio_cal/xd02/texpass/families.py <L4>` lists each texture with the family maps that use it).

Kept from no shipped dungeon, each a stand-in listed below: `warnsign` (the clan's skull warning, a clicked sign the
brief asks for: nothing shipped shows a warning board), `runeeyvlij` (the chalk mark, a clicked clue: nothing shipped
shows a mark on rock), `web32n735s` (the web wall and the cocoon must read as web: no shipped dungeon has a web
texture). Kept from outside the families: the pool contents `7slimywtr` (green, a liquid), `lavatyl` (red, the lava
shader without the lava flag), `orertlga` (gold, stand-in), the bronze plaques `sign22` (tallies, stand-in) and
`sign128` (the tablet), and `sky_clo1` (daylight in the two exit faces).

Looked at in the game as whole pictures for motifs: `t3dr1` has a bronze roundel with a griffin and two carved
fleury crosses in its lower panel (6d05's own door; read as dwarf work); `d7wl1ctr` carved faces in its frieze,
`d7ceil2` carved sigils, `d7flor4` runes, `d7dor1` carved faces, `d7dor3` a carved skull: 6d09's own dwarf ornament.
No windows, portholes, signs or symbols of another place in the new set.

### Textures to generate

| What it shows | Size | Where it goes | Stand-in now |
|---|---|---|---|
| Gold seams in red worked rock: `t3ll5` with bright veins, and the same in `t3ll6` and `crstont` | 256 x 256 each, tiling with their rock | the six vein switches (`off`): sorting floor and rim in `t3ll5`, the stope's three in `t3ll6`, the flood's in `crstont` | `c1gold` (7d34's dark rock with gold): reads as a seam on `t3ll6`, as a dark patch on red `t3ll5` |
| Ore-cart side: a riveted iron tub side with a rolled rim | 128 x 64 | side boards of the trestle car and the east cart; the sides of the four standing carts | `ch1topb` stretched (grey iron-banded planks: a box more than a cart) |
| Pool basins: wet stone with a mineral crust in the pool's colour (red, gold, blue, green) | 128 x 128 each | the sunk levels' edges and floors and the pool platforms' sides | the room's rock (`crstont`, chapel `d7trim8`) |
| Gold pool water: shallow water over gold sand (a picture; the liquids have no gold) | 128 x 128 | `platform:gold_pool` top | `orertlga` (an MM6 temple's marbled gold-brown) |
| Chalked tallies on dressed stone: rows of strokes and dwarf numerals | 256 x 128 | the tally room's four wall panels | `sign22` (bronze plaques) |
| A Red Dwarf chalk mark on red rock | 64 x 64 | `panel:chalk_mark` over the dry-stone wall | `runeeyvlij` (a carved rune band) |
| The clan's warning: skulls daubed in red on rough planks | 256 x 128 | `panel:clan_sign` in the adit mouth | `warnsign` (printed-looking skulls on parchment) |
| Thick old web over dark rock, opaque | 128 x 128 | `door:web_wall`, `chest:cocoon` | `web32n735s` |
| Optional: an iron grille gate | 128 x 256 | `door:hoist_gate` (the brief's iron grille) | `d2ceil1` slatted timber |
| Optional: dark, rusted iron | 64 x 64 | rails, buffer stops, hoist cage | `ch004i` (bright clean steel under the lamps) |

### What I was unsure of

- `ch004i` is the Red Dwarf Mines' own iron but reads as bright new steel: the rails are white stripes under the lamps
  (01, 02, 13) and the hoist cage is shiny (29). Pass 1's darker iron came from no shipped dungeon. A dark rusted iron
  is on the list.
- `cbedsqr` (6d09's furniture wood) is a plain bright orange slab on the tally table and the pay rack (10, 18);
  6d09's tables are cabinets the studio cannot build. Pass 1's plank table read better there.
- The spider galleries' `crstont` reads green under the fungus light (32, 33): cave stone, but a colder place than the
  rest of the mine.
- The stope from below (28) is now red bench faces against dark pit walls under a gravel roof, clearer than pass 1's
  one-texture drum, but still tiers: the brief's funnel needs geometry (rock between the benches), not textures.
- `t3dr1`'s crosses: kept as 6d05's own ornament.
- `plan.yml`'s theme notes still name pass 1's textures (the plan is L3's record; not edited).

### What was scripted, checks, pictures

- One-off script `output/studio_cal/xd02/texpass/retex.py` over rooms.yml and objects.yml (themes rewritten, each
  room's theme, each surface by its room and role; its whole diff checked), then two global swaps (`bemh32c` to
  `t3d2abe`: 6d05's orange beam read bright orange beside its dark posts in the first look; `d2ceil3` to `d2ceil4`: the
  same picture) and one hand edit (the tally door). Doors `mole_rock` and `strongroom` gained `tile: true`; chests
  gained `end_surface`.
- `oymap fmt` clean, `oymap validate` no issues; the build's five warnings are pass 1's (placed monsters' names).
- Playtest: 171 steps, four runs of four pass (`output/studio_cal/xd02/run2/four.out`, logs `final_1.log` to
  `final_4.log`; `texpass/test.sh` builds, installs and runs them).
- Pictures: `output/studio_cal/xd02/shots2/` (the same 35 cameras as `shots/`, `captions.yml`, `plan.png`, `iso.png`;
  shape unchanged); before/after sheets `texpass/fin_1.jpg` to `fin_9.jpg`; door, chest and cart close-ups
  `texpass/look2/`; the first look `texpass/look1/`. `texpass/tour.sh` installs a build into the scratch root (copies
  that unlink first) and takes a tour.

## Generated textures (2026-11-13)

The "Textures to generate" list above, made by Codex image generation with the family's shipped masters as
references and installed in `output/studio_play/xeen_root` only (sources, prompts, raw returns, checks:
`level_generation/textures_xeen/`, its README). Every texture is x4 art (master 4x the size below).

| Name | What | Size | Family | Where used |
|---|---|---|---|---|
| `xngold5` | Gold veins painted into 6d05's `t3ll5` (the rock is the master's own pixels) | 256 x 256 | MM6 Snergle's Caverns `t3ll5` | `switch:vein_sorting`, `switch:vein_rim` |
| `xngold6` | The same in `t3ll6` | 256 x 256 | `t3ll6` | `switch:vein_rich`, `vein_se`, `vein_sw` |
| `xngoldcr` | The same in `crstont` | 256 x 256 | `crstont` | `switch:vein_flooded` |
| `xncartsd` | Riveted iron tub side, rolled rim, two strap bands, rust | 128 x 64 | MM6/MM7 iron (`ch1frntb` bands, `ch004i`) | sides of the four standing and two tipped carts (tipped carts' up faces too), side boards of the trestle car and the east cart |
| `xnbasred` | Wet blue-grey basin stone crusted red | 128 x 128 | `crstont` | red pool: its level's edge and floor, the water platform's sides |
| `xnbasgld` | The same crusted ochre-gold | 128 x 128 | `crstont` | gold pool basin |
| `xnbasblu` | The same crusted turquoise and blue | 128 x 128 | `crstont` | blue pool basin |
| `xnbasgrn` | 6d09's dressed blocks crusted moss-green and verdigris | 128 x 128 | MM6 Snergle's Iron Mines `d7trim8` | green pool kerb |
| `xngoldwtr` | Shallow water over gold sand and nuggets, from above | 128 x 128 | MM6 water / MM7 gold | `platform:gold_pool` top |
| `xntally` | Dressed sandstone slab covered in chalked tallies and dwarf numerals | 256 x 128 | 6d09 `d7wl2ctr` | the tally room's four panels |
| `xnchalk` | A chalked strongbox, an arrow and two strokes on `t3ll5` (painted into the master) | 64 x 64 | `t3ll5` | `panel:chalk_mark` |
| `xnclansgn` | Three rough planks daubed in red: three skulls, MAD DWARF CLAN, DIG ELSEWHERE | 256 x 128 | 6d05 planks (`d2ceil2`, `t3dr1`) | `panel:clan_sign` |
| `xnweb` | Thick matted web over dark rock, opaque | 128 x 128 | `crstont` behind web | `door:web_wall`, `chest:cocoon` |
| `xngrille` | Riveted dark iron grille, see-through (alpha) | 128 x 256 | 6d05 iron | `door:hoist_gate` (both sides) |
| `xnrustirn` | Dark wrought iron with rust and pitting | 64 x 64 | 6d05 iron / `ch004i` | every former `ch004i` surface (111: rails, buffer stops, wheels, hoist cage, chain, brake wheel, points lever, winch ends) |

How they were made to sit in the set: the veins and the chalk mark are edits of the shipped masters, kept only where
the model changed them, so the rock round them is the wall's own; the switch shows a 192 x 128 window of the master
(the chalk panel a 160 x 80 one) centred on the vein, so its rock is at the wall's scale and the old dark rectangle
of `c1gold` is gone (`01`-`06-vein`). The basins, water, web and iron tile (3x3 checked); signs, slab, cart side and
grille are single pictures made at their faces' proportions (the grille 192 x 320, the cart side 224 x 72, the
clan sign 2:1).

Pictures: `output/studio_cal/xd02/textures_gen/before/` and `after/` (same cameras; `pairs.jpg`). Notes from looking:
the veins now read as gold in the rock, not a patch; the hoist gate is a see-through iron grille; the carts are iron
tubs; the rails are dark iron instead of white stripes; the clan sign and chalk mark are readable (the mark small at
range, as a clue). The web wall shows reddish from the galleries: it is a secret face and the game's secret pulse
tints it (the stand-in had the same tint). Not shown: `switch:vein_flooded` has no clear view from the flooded working
in either build (`oymap things`: "no place with a floor and a clear view found within 176 of it"; `04-vein-4` shows
rock in both): a placement issue, not a texture one. The tally slab reads as an even grid of strokes, plainer than
the bronze plaques it replaced.

Playtest on the play root after the change: `playtest.yml` 4 of 4, 171 steps
(`output/studio_cal/textures_gen_tests/four.out`).

## Second pass: the user's lessons (2026-11-13)

The user had not played XD-02; this pass applies what he found in XD-01 and XD-04 (REBUILD_PROCEDURE.md "What the
measure does not see" to "Textures for a new dungeon") and the ninth merge's checks. The project before it is in
`output/studio_cal/xd02/pass2_backup/`; scratch in `output/studio_cal/xd02/pass2/` (`go.sh` builds against the play
root's assets, where the generated textures live, and installs into the private root `root/`, a hard-link copy of
`output/studio_play/xeen_root`; `root_before/` keeps the play root's three map files as they were; `test.sh` runs the
playtest). Scripted, each a one-off whose whole diff was read, in order: `edit_p2.py` (five rooms enlarged with their
contents), `edit_p2b.py` (the Deep Line station, findings, chests, levers), `edit_p2c.py` (the tablet), `edit_p2d.py`
and `edit_p2e.py` (carts, trestle, hoist, exit), `edit_p2f.py` and `edit_p2g.py` (ledge torches, head frame),
`edit_p2h.py` to `edit_p2k.py` (what a player reads, the brake, the winch, the points), `edit_p2l.py` to
`edit_p2n.py` (carts again, after looking); two hand edits (a capstan bar's height, two doors' titles). The project
files are the source; none of these is to be run again.

### Room sizes (`scale_bands.py`, `pass2/scale_before.txt`, `scale_after.txt`)

| Figure | Before | After | Shipped p25 / median |
|---|---|---|---|
| Bigger rooms: upper-quarter room floor area | 0.93 M (20th percentile, below p25) | **1.80 M (53rd)** | 1.06 M / 1.64 M |
| Largest room | 5.62 M | 5.62 M | 3.68 M / 6.13 M |
| Typical ceiling height | 482 | 504 | 394 / 521 |
| Taller rooms: upper-quarter height | 640 (56th) | 640 (56th) | 522 / 570 |
| Typical doorway width | 256 | 256 | 256 / 256 |
| Floor area (`metrics`) | 37.7 M | 42.0 M (M band 40-70) | |

The upper quarter is the 12th largest of 43 sectors as `oymap metrics` counts it, so twelve rooms had to reach the
median; six did (stope floor, flooded working, Turntable, chasm, spider galleries, mess hall). Per room (sector floor
area as the measure counts it, platform tops included; `pass2/sectors_before_named.txt`, `sectors_final_named.txt`):

| Room | Before | After | What changed |
|---|---|---|---|
| Red Dwarf chapel | 1.43 M (octagon 1280, 512 high) | 1.94 M (1408 by 1600, 576 high) | the octagon drawn out 1.1 east-west and 1.25 south from its door wall and set 64 east (clear of the stope rim); pillars, rocks and braziers moved with it, the pool, kerb and stone lantern kept at their size round the new middle; the tablet now a plaque in the south wall (below) |
| Adit mouth | 0.97 M (1024 by 768) | 1.92 M (1280 by 1280) | 256 east and 256 to north and south: the portal hall; timber sets, rails, posts moved; the cart against the north wall, the sign beside the drift's mouth |
| Top Station | 1.52 M (1280 by 896) | 1.90 M (1664 by 896) | 384 east, a fourth timber set; the barrels moved with the east wall |
| Deep Line station | 0.67 M | 1.87 M | a marshalling bay south of the rails (to 1230 by 1860): a rail spur, a spoil heap, barrels, a lantern, a torch, a spider spawn |
| Tally room | 0.73 M (hexagon 896, 448 high) | 1.80 M (1434, 576 high) | the hexagon 1.6 times about its door wall; tallies on two slabs a wall, two more torches; the table, the tallymaster behind it and the strongbox behind him, west |
| Sorting floor | 1.50 M (1408 by 1024) | 1.70 M (1408 by 1216) | 192 further north: chutes, lintel, beams, ore and spawns moved with the wall |
| Bunks, chutes, crawl, grottoes, drifts, burrow, strongroom | | unchanged | small on purpose, or tunnels |

The plan and order are the brief's: the same rooms joined the same way in the same places. `oymap solve` opens it in
the same steps (0: 7 sectors; 1: to 27; 2: to 35; 3: needs item 2111, to 37; 4: the winch), 37 of 43 reached, the six
others the bunk shelves and the chutes as before (`pass2/solve_after.txt`). Not enlarged, though the lead's list names
drifts: the haul drift (0.77 M) and foot drift (0.85 M) are 384- and 320-wide tunnels whose widening would have run
into the sorting floor and the station; the stope rim (0.44 M) lies between the pit and the chapel.

### Each rule and how it is met

Pictures: the interactive things before (`pass2/things_before/`, the play root's build, `b1.jpg` to `b3.jpg` sheets)
and after (`pass2/things_after/`, `contact.png`); rooms and props before | after `pass2/pairs_1.jpg` to `pairs_6.jpg`
(where the old room was smaller the before camera stands in rock: compare `shots2/` for those), close-ups
`pass2/shots_after2/`, final tour `pass2/shots_final/`.

- **Faces in one plane** (the lead's count): 54 pairs before, **0** after. Trestle caps and ties now span between the
  legs' inner faces (they crossed the legs' faces and tops); winch and fall parts apart; the flooded working's two
  walkways meet instead of overlapping; the lamp rack's posts end under its shelf; the haul drift's posts 36 wide
  under 32-wide caps; the sorting floor's lintel inside the room (it ran into the chute openings' reveals); the rim
  ledge's two rails at different heights where they meet; the hoist cage's corner posts proud of its rails; the Deep
  Line exit face the whole end wall (it lay over the wall); the capstan's bars at two heights.
- **Lootable things read as lootable, nothing else looks like a chest:** the footlockers, payroll chest and strongbox
  are `kind: ch1` (end, middle, end; they were one picture stretched), all named **Chest** (they were Footlocker,
  Payroll chest, The clan's strongbox, Web-wrapped bundle); the cocoon is now a web-wrapped body on the floor (a
  block in `xnweb`, not clicked) with the miner's ch1 Chest beside it; the noose corpse (Corpse08, a hanged man) is a
  lying skeleton (`dec05`). The winch was a plank box between posts and read as a crate or dresser: it is a capstan
  (an eight-sided timber drum, an iron head, two bars). The carts (the user's "carts read as crates"): every cart now
  stands on four iron wheels outside a timber chassis, its tub flaring from 180 by 100 to 200 by 120 with the
  generated cart side at its own 2:1 shape and ore heaped in it; the three tipped carts (boxes on their sides) became
  carts left off the rails, since a box on its side read as a crate even with ore spilled from it
  (`shots_after2/01-adit-cart.png`, `06-stope-cart.png`, `07-stope-cart-2.png`). They still read as iron tubs more
  than as mine carts from far off (no curved tub, no model).
- **Hover names and reasons:** every clicked thing has one (`pass2/things_after.txt`: 44 things, the rockfall's step
  plate the only one without, as XD-01's: it is stepped on). Doors are Door / Plank door / Carved stone doors.
- **Signs and long texts:** the clan's warning (now "Warning sign") opens a message window (`window: true`), as the
  chalk mark and the tablet do; every status line is now under 65 characters (points, car locks, web, winch, brake,
  vein, exits); the longer explanations (the brake without its key, the rim's hoist lever before the cage is ridden)
  are message windows.
- **No silent clicks:** a mined vein says "Only bare rock is left where the seam was" (a condition with
  `locked_text`: with `else_effects` the build flips the switch back to its gold picture; `pass2/build2` Lua showed
  it), the winch's second turn "The winch's rope hangs slack: the fall is gone", the freed brake "The chain lies
  slack in the rail bed", the rim's hoist lever before the cage was ridden explains the brake in a window. The
  playtest asserts each.
- **Puzzles a player can solve; no riddles:** none is typed. The clues: the chalk mark (sorting floor, clicked, a
  window: a strongbox and an arrow into the wall) before the strongroom's dry-stone wall; the chapel tablet (a
  window: "THE BLUE SLEEPS BEHIND THE SILK") before the web wall; the Deep Line's brake now says where its key is
  ("the clan keeps it, with the tallymaster in his tally room off the mess hall"); the west adit's exit says "The
  winch might drag it away" beside the winch; the cars' locks name the points at the Turntable, whose lever is beside
  the disc with the green lamps.
- **Nothing floats or hangs from nothing, nothing inside something else:** the hanging braziers (`brzier00`, a bowl
  on a chain) stood on the floor in the Turntable, the mess hall, the Top Station and the chapel. In the station and
  the mess hall they now hang from cap beams (height 300 under a beam 448 up: the chain's top in the beam,
  `shots_after2/02-station-brazier.png`); in the Turntable and the chapel, which have no beams, they are standing pole
  torches (`dec56`). The spiral's five ledge torches stood inside the rock benches (a wall decoration's
  `floor_height` is not used: they were at the stope floor + 200, z -952); now at heights above the room's floor that
  put them 200 over their ledges. The lamp room's five unlit lamps were on the wrong wall, one inside the torch: now
  over the rack on the east wall, the shelf touching that wall. The sorting floor's chandeliers reach their beams;
  the tallymaster no longer stands in his table; barrels, wheels, the head frame's cross-head (now a sheave beam out
  of the rock between the arms) and the repair niche's cart (on two blocks) all stand on something.
- **No stretched pictures:** the chests (above), the flatcars' side boards (the cart side at 8:1, now iron at its
  size), the standing carts' sides (2:1 faces), the tablet (a wall panel at the plaque's own 2:1; its plinth's ends
  were squashed), the chalk mark (square, at its 64 by 64). Left: the trestle's X braces' raked end faces, 16 by 24,
  inside the legs and never seen (the build lays a raking beam's ends that way; any texture shows it).
- **Doors and switches of the area's family:** the six car and hoist levers are MM's lever (`kind: lever`: post
  `t3d2abs`, arm `t3d2abe`, 6d05's timber); the points lever an iron lever on its post (its handle down while the east
  line is live: a `switch` preset now, inverted so the first pull moves it); the brake a hand wheel with four handles
  on an iron-capped post (a clicked block; a lever's handle would spring back on the freed brake's second click).
- **Named things recognisable:** the veins read as gold in rock (`things_before/b3.jpg`); the flooded working's vein,
  invisible before (behind a stalagmite on a corner wall), is on the east wall beside the dry hump's opening, seen
  from the planks (`pairs_6.jpg`, top); the pools read as pools; the rails and cage are dark rusted iron
  (`xnrustirn`, checked: no white stripes); the cocoon, the winch and the brake as above.
- **Nothing in its stand-in:** no new texture was needed; every stand-in of the texture pass had been generated.

Playtest (`playtest.yml`, now 182 steps): new coordinates in the enlarged rooms; the clan sign, tablet and rim lever
as message windows; the second clicks of the sorting vein, the winch and the brake asserted. Four runs of four on the
final build in the private root (`pass2/final.out`, logs `pass2/run/final/`), and one more on the play root after
installing it (`pass2/run/playroot/`), all 182 steps. Installed into `output/studio_play/xeen_root` (map, scene, Lua
and `map_stats.txt` byte-identical to the tested private root); the project's `ids.lock.yml` is the final build's,
and a fresh build from it is byte-identical to what was installed.

### What waits on the studio

- `uneven: true` on a surface: the build's squash warning tells you to say it, the schema refuses it
  ("unknown key"); the lowering reads it (`IndoorLowering.cpp` `readSurface`).
- A wall decoration's `floor_height` is ignored: the height counts from the room's floor (the ledge torches).
- `oymap metrics <file> --assets <root>` (and so `scale_bands.py`) measures the root's map of the same name, not the
  file given: run it on the installed copy of the root it names.
- The build warns that the brake's failing branch shows nothing: it does not read `lua` in `else_effects` (a window
  or a line in both cases, asserted by the playtest).
- `oymap audit` calls the two mess hall braziers and the station's `thing.floating`: the build accepts them
  (`hangs: true`, chain top in the beam); the audit does not know a decoration hangs from a beam (XD-04 saw the same).
- A switch with `condition` and `else_effects` turns back to its `off` picture in the failing branch, so a mined vein
  would show gold again; `locked_text` alone avoids it, but a lever cannot then say two different things.
- No curved shapes: the carts' tubs, the capstan and the brake wheel are prisms.

### What looks worse

- The bigger rooms have the same lights plus a few; the adit's and the tally room's far corners are darker.
- The carts no longer lie tipped in three places: the brief's "tipped" and "lying" carts stand off the rails.
- The tally room's slabs repeat the same picture twice on each wall.

## Third pass: the user's walk (2026-11-13)

The user played the second pass (play root `output/studio_play/xeen_root`) and said "otherwise this dungeon is good",
with six points. The project before this pass: `output/studio_cal/xd02/pass3_backup/`; scratch
`output/studio_cal/xd02/pass3/` (`go.sh` builds against the play root's assets and installs into the private root
`root/`, a hard-link copy of the play root; `tour.sh` takes a tour there; `test.sh` runs the playtest). All edits by
hand (two small Python replacements whose diffs were read). The lead's captures of the user's places:
`output/studio_cal/xd02/user_walk1/shots/`. Pictures: before `pass3/shots_before/`, after `pass3/shots_after/`,
`shots_levers/`, `shots_levers2/`, `shots_rim/`, `shots_final/`, `arrive_timer.png`; before | after sheets
`pass3/pairs_1.jpg` (bats, chest, strongroom), `pairs_2.jpg` (the four cart stops), `pairs_3.jpg` (brake, arrival,
Tallymaster, footlockers).

1. **"Bats stuck"** (sorting floor, looking up at the chutes). `spawn:chute_2` stood in the middle ore chute, a room
   whose floor is 384 up the north wall: the bats spawned there and never came out (in `shots_before/02-chutes-wide.png`
   a Giant Bat hangs in the chute). The spawn is now `spawn:sorting_south` on the sorting floor's south side
   (13350, 5900), about 1000 from the chute mouths (a flier's idle wander heads back toward its spawn point, so it
   does not drift up into them); the chutes' notes say nothing may spawn in them. Checked every monster: the 11 placed
   ones stand in reached rooms (the burrow's moles behind the rock that the rich vein opens; the flood's moles on its
   water floor, which the party walks); `oymap audit --reach` now names one unreached spawn point only, the item on
   the second bunk (an item, 200 from the bunk cut's floor: within the game's 512 item reach by its code, not tried in a run), where it named the chute
   bats before. After: `shots_after/03-chutes-wide.png`.
2. **"Bad chest texturing"** (the payroll chest in the forgotten strongroom). The kind fits: `ch1` is the chest of both
   families (6d09 lays ch1frLE/ch1frntB/ch1frRE on its chests' fronts; 6d05 the plain ch1). What else was wrong: the
   chest was 160 by 96 where the shipped ch1 is 96 by 64, so its middle repeated and the front showed two locks and
   two hasps; it stood end-on to the doorway (the party saw the handle end first); the lid's end strips lay crosswise
   (the studio's fault, fixed by code batch ten, not worked round). Now the shipped size and its front to the door
   (`facing: n`). The same faults on the two footlockers (160 by 80, end-on to the cut: now the shipped size, fronts
   to the cut) and the strongbox (end-on: turned); the lamp room's chest was the world default, MM7's `7gt002`, beside
   the 6d05 timber: now `ch1`. Left: every studio chest has its lock front on both long sides (the shipped ones stand
   against a wall with no back). After: `shots_after/04-chest-user.png`, `25-bunk-footlockers.png`,
   `08-lamp-room-chest.png`.
3. **"What are these wood things supposed to be?"** The user stood in the strongroom's sunken doorway (the capture
   stands inside the shut dry-stone wall; the room was not enlarged). In front of him: the brief's "empty pay rack" (a
   96 by 64 block 192 high in `cbedsqr`, a bright orange slab) and the "fallen stool" (a 96 square block 40 high, the
   same). The stool is gone; the pay rack is a timber rack of two plank shelves on two posts against the south wall
   (6d05's timber `t3d2abs`/`d2ceil2`/`t3d2abe`, as the lamp rack), which reads as shelves. Before
   `shots_before/04-strongroom-open.png`, after `shots_after/05-strongroom-open.png`,
   `shots_levers2/10-strongroom-rack.png`.
4. **"How am I supposed to press that lever while being on the moving platform?"** Every car lever was a call lever on
   the far side of its gate's wall: the station's on the loading platform, the Turntable's in the Turntable, the east
   cart's in the Turntable and on the landing. A rider could only click the car itself, which nothing tells him. Each
   of the five stops now has a riders' lever beside the gate on the line's side, facing the deck at the deck's height
   and within reach of it (about 90 from the deck's edge): `switch:trestle_ride_station` (chasm east wall),
   `trestle_ride_turntable` (chasm west wall), `east_ride_turntable` and `east_ride_landing` (the east line's north-east
   wall; a torch `deco:east_line_end_torch` and `light:line_end` light the landing one, which stood in the dark), and
   `hoist_ride_rim` (the pit wall past the cage's east corner, arm at 170 above the cage floor so it shows between the
   cage's middle and top rails; clear of the cage's frame). The hoist's floor lever already stood in reach of the
   cage; it no longer refuses before the first ride ("step in and work its lever", which no lever on the cage
   answered): it sends or calls the cage and takes off the brake for the rim's bell-pull. The call levers stay for
   calling a car that is away. Before `shots_before/08`, `10`, `12`, `14`; after `shots_levers/01`, `03`, `05`,
   `shots_levers2/09`, `shots_rim/02-rim-lever-a.png`, `shots_levers2/01-hoist-floor-lever-from-cage.png`.
5. **"Pressed this, not sure what it was supposed to do?"** (the brake wheel). It was named "Brake wheel"; with the key
   it said for two seconds "The brake key opens the padlock: the chain falls away" while a thin chain dropped 52 into
   the rail bed, and the way on was a click on the dark face at the end of the cutting (`shots_before/24-brake-used-before.png`).
   Now: hover **Deep Line brake**; without the key the window as before (the cart is chained here, the Tallymaster has
   the key); with it a window: the key opens the padlock, the chain drops off the cart, the brake comes off, "climb
   in at the buffer stop and it will run down the Deep Line to the Clan King's Deep Mine"
   (`shots_after/22-brake-used.png`); the **cart itself is clicked** to ride down (`evt:deep_cart`, hover "Deep Line
   cart", "The cart is chained to the brake wheel by the north wall" before; a `lua` MoveToMap with exit:deep_mine's
   arrival, since an exit sits only on a wall face: gap 6; change it with the neighbour when XD-03 exists); the exit
   face stays. On first entering the station the status line says "The Deep Line: the clan's cart stands at the buffer
   stop, chained to a brake wheel." (5 s).
6. **"I don't know the intention of it, what quest was there"**. A window a moment after first entry (QUESTS.md M3):
   "Mayor Gunther of Vertigo sent you here. The Mad Dwarf Clan has taken the Red Dwarves' mine, and their Clan King
   holds the Deep Mine below it. The way down is the Deep Line cart at the bottom of the Open Stope, past the
   Turntable; the clan keeps it chained, and their Tallymaster holds the brake key in the camp north of the
   Turntable." (`pass3/arrive_timer.png`). It is a one-shot timer (`every: 1`, `once`): a `load` event's message
   window is never shown and a `step` event does not fire where the party starts (both tried; repro: build the
   project with `trigger: load` and play `pass3/arrive_test.yml`, whose dialog assert fails though the event ran).
   The goals on the way: the Tallymaster is a **Dwarven Lieutenant** (230, level 20, 100 hit points; was a Soldier like
   his guards), so he stands out in blue among the green Soldiers and the hover names him apart (XD-03's Clan King is
   the Commander, 231; harder than the brief's level-10 boss: `hp: 80` is still ignored); entering the tally room
   says "The Tallymaster and his guards! The clan's strongbox stands behind his table." (5 s); the strongbox says it
   holds "the Deep Line's brake key". Nothing is brought back from this map (M3's Red Dwarf Badge comes from the Clan
   King in XD-03). After: `shots_after/24-tally-boss.png`.

Also, from the tenth merge's binary: the chalk mark's text is now a status line (only signs, tablets and the like open
a window); the red and gold pools' tops carry `liquid: liquid` (the build warned of `lavatyl` without the fluid bit;
both now ripple as the shipped liquids do: `shots_final/05-red-pool.png`, `06-gold-pool.png`).

Checks: `oymap validate` no issues, `fmt --check` clean; build warnings: the brake's `else_effects` Lua (known) and
one squashed beam face (pass 2's); `oymap audit`: 0 faces in one plane. Playtest (now 191 steps: the arrival event,
every new riders' lever used from its deck, the trestle car up and down again by them, the hoist up by the floor lever
from inside the cage and down by the rim's riders' lever, the Tallymaster's absence after the fight, the tally room's
and the station's entry texts, the brake's window, the cart refusing while chained and then carrying the party out):
four runs of four on the final build (`pass3/final2.out`, logs `pass3/run/final2/`), one more on the play root after
installing (`pass3/run/playroot/`). The headless runner does not open windows from timer events, so the playtest
asserts that the arrival event ran (its once variable); the window itself is pictured in a desktop run.

General lessons (for other maps): a spawn point goes on a floor the party walks, never in a niche, shelf or shaft a
flier can sit in; a chest takes its kind's own size (wider repeats the lock) with its front toward where the party
comes from; a block that stands for furniture must read as that furniture or go; every ride has a lever at each stop
on the rider's side; a mechanism that changes something out of sight says in a window what changed and where to go
next, and the thing the player expects to use (the cart) does it; a new dungeon opens with its errand and names its
boss when he is met.

## Exits to Vertigo (2026-11-13)

`exit:x1_adit` (the portal, evt:exit_x1 21) now leads to X1 (`xeen_x1.odm`): arrival [-10240, 16131, 1184], facing 270
(south, downhill), in front of X1's mine portal (`thing:mine_portal`, face at y 16531). Unchanged: `exit:deep_mine`
(the cart; also the Lua line in `evt:deep_cart`) and `exit:x4_adit` still go to Emerald Island (no X1 door matches
them; XD-03 and X4 are their places). `playtest.yml` gains, after the cart, a reload of the mine at its portal start,
the portal exit, the map and position on X1 and a walk off down the lane.

Backup before the change: `output/studio_cal/xd02/exits_backup/`. Build `output/studio_cal/xd02/exits_build/` (against
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
`relations` (the build's load event `evt:studio_relations`). Written into objects.yml by
`output/studio_cal/hostility/add_relations.py`: the Dwarves (229-231) the party's foes (they were, by the Lua load event
`evt:clan_hostile`, now dropped by `drop_clan_lua.py`: the word says it) and kept from the Spiders (400-402) and the
Troglodytes (412-414), both ways. `playtest_hostility.yml` (written by
`output/studio_cal/hostility/gen_hostility_tests.py`) checks the slot and placed foes hostile, the peaceful ones
peaceful and the map's kinds, spawned side by side near the party, not taking each other on; it passes twice, as do the
map's other playtests.

## Rebase, phase 0 (2026-11-20, lane A7)

The design part of the rebase (`devdocs/xeen/CHANGES_FOR_BUILT_MAPS.md` A1-A3, A5, A7, XD02-1 to XD02-3) and the texture
trim (ROADMAP §5.2, dungeon M cap 45). Still `world: mm7` on MM7 stand-in rows: the Xeen world package, its rows and
hooks do not exist yet. Backup of the project before: `output/studio_cal/xd02/a7_backup/`; work, builds, logs and
pictures: `output/studio_cal/xd02/a7/` (build `output/studio_cal/xd02/a7_build/`); asset root
`output/studio_cal/a7/root_mines` (a hard-link copy of `assets_dev` with the Xeen stand-in maps). Edits by hand (small
Python replacements whose diffs were read), then `oymap fmt` and `oymap record --author agent:xeen-a7-mines`.

**Monsters** (`output/studio_cal/a7/count.py xd02`: spawn points times the mean per marker, plus placed):

| | Before | After |
|---|---|---|
| Monsters | about 71 | **about 56** (MAPS §0: 55) |
| Levels | 3-30 (the ten untiered Dwarf spawns rolled Soldier 10, Lieutenant 20 or Commander 30; the Tallymaster a Lieutenant 20) | **3-10** |
| Monster spawn points | 23 | 18 |
| Placed | 11 (the Tallymaster a named Lieutenant 230 with `hp: 80`, `immobile`) | 11 (four tally room guards, all Dwarven Soldiers 229) |

- `project.yml` slots: Dwarf difficulty 1 -> 0 and Spider 2 -> 0 (rest encounters too: every Dwarf a Soldier 10,
  every Spider a Giant Spider 5), Bats 2-4 -> 2-3 a marker. The seven Dwarf spawns left say `tier: a`.
- Spawn points dropped where the map was densest: `spawn:mess_leg` (the mess hall keeps two, beside the bunk cut's and
  the tally room's four), `spawn:turntable_s` (the Turntable keeps a Dwarf and a Spider point), `spawn:galleries_mid`
  (the galleries keep one and the cocoon's three), `spawn:stope_floor_s` (the stope floor keeps one Dwarf and two Spider
  points) and `spawn:sorting` (the sorting floor keeps pass 3's `spawn:sorting_south`, far from the chutes).
- **The Tallymaster is an ordinary Clan Guard** (CHANGES A1: XD-02 has no boss): Dwarven Soldier 229, no name, no
  `hp`, no longer `immobile`. He carried nothing; the brake key was and is in the strongbox behind him. The id
  `monster:tallymaster` stays (the lock). The texts that named him now name the strongbox: the arrival window ("the
  brake key lies in their strongbox in the tally room"), the brake's window, the tally room's entry line ("The clan's
  tally room: its strongbox stands behind the tally table.").
- Kinds are unchanged (Dwarves 229-231, Spiders 400-402, Troglodytes 412-414, Bats 205-207), so `relations` and
  `playtest_hostility.yml` stand as they were.

**Treasure:** map_stats treasure level 2 -> **1**; the payroll chest 3 -> **2**, the strongbox 2 -> 1, the cocoon's
chest 2 -> 1; the footlockers and the lamp room's chest were 1; both item spawns were 1. Fixed contents unchanged (the
payroll's 400 gold and amethyst, the strongbox's 150 gold and the brake key).

**Original lines** (CHANGES XD02-3, A5; the source text `reference/mm4_5_world_of_xeen/unpacked/text/xeen/`, the
dwarf mines are `aaze0033` to `aaze0035`):

| Line | Source | Where |
|---|---|---|
| "Scribbled on a piece of parchment, a note reads: 1 bottle orc's milk, 2 boxes of Dwarf biscuits, 1 can of split toadsoup, and one everlasting stick of troll jerky." | aaze0033 #9 | the mess hall's provisions barrel (`deco:mess_hall_64`, hover "Barrel", `evt:barrel_note`, a message window), as the original keeps its notes in barrels and crates |
| "Scribbled on a piece of parchment, a note reads: There are many DEEP mines." | aaze0034 #14 | the keg by the brake wheel at the Deep Line's head (`deco:deep_station_100`, "Barrel", `evt:deep_note`, a window) |
| "The mine car doesn't move." | aaze0033 #25, aaze0034 #30 | the chained Deep Line cart's locked line ("... it is chained to the brake wheel.") |
| "A cave in!" | aaze0033 #34, aaze0034 #31 | the foot drift's rockfall ("A cave in! The rotten props give way and rock thunders down.") |
| "The barrel is empty." | aaze0033 #5 | the barrel beside each note (`deco:mess_hall_65`, `deco:deep_station_101`), so the two barrels side by side read alike |

**Exits** (CHANGES A7): `exit:deep_mine` now leads into XD-03, `xeen_xd03.blv` at its start, the foot of the Deep
Line ([8192, 1088, 384], room:deep_line, facing west over the Deep Landing); the cart's own click (`evt:deep_cart`,
Lua) repeats it. A move into another dungeon asks no question (Emerald Island did), so the playtest no longer answers
one. `exit:x1_adit` leads to X1 as before. `exit:x4_adit` is **still a stand-in** (Emerald Island): X4 is built in
phase 2 (ROADMAP §6); change its `to`, `arrival` and `direction` then.

**Doors (XD02-4, optional): not done.** The 34 door records are 15 doors, 6 movers (two carts, the hoist, the chain,
the fall, the rubble) and their gates; every one opens a way, guards a ride or is a secret: none goes cheaply.

**Textures** (`oymap metrics <installed blv> --world mm7 --assets <root>`, palette.textures): **48 -> 45**
(`texture_use.py --project`: 41 -> 38; the built map also counts the chest set and other build-side pictures). Three
repeats inside the 6d09 / 6d05 families, each a small surface:

| Was | Now | Where | Why it costs no look |
|---|---|---|---|
| `mnwl2` (6d09 smooth rock roof) | `d7ceil2` | the forgotten strongroom's ceiling (one face) | the same family's carved ceiling of the chapel and tally room; reads as dwarf work (`shots/06-strongroom-roof.png`) |
| `cbedsqr` (6d09 furniture wood) | `d2ceil2` top, `t3d2abe` sides | the tally table | the camp's long-table timber; the old one was the bright orange slab pass 1 called weak (`shots/04-tally-table.png`) |
| `d7dor3` (6d09 skull door) | `t3dr1` | the tally door (theme dwarf_hall) | the camp's plank door, as the bunk door beside it in the same mess hall; the tally room behind keeps its 6d09 walls |

**Checks** (from `openyamm-studio/build-xeen/oymap` and `build-xeen/game/openyamm`, the binaries of A1's merge
point 1): `validate` no issues; `build` 3 warnings, all older (the four moles' name "Tiger Mole", the brake's
`else_effects` Lua, one squashed beam face); installed into the root; `audit --reach --solve`: 0 faces in one plane, no
dead handler, nothing stranded or waiting, the brake key (item 2111) reached in wave 3, never reached only the three
bunk shelves and three chutes (by design), the three hanging braziers' `thing.floating` (known); `fmt --check` clean;
`playtest.yml` (207 steps: new are the shopping list's window, the empty barrels, the cart's original line, the Deep
Line note's window, and the arrival in XD-03 at its start) **4 of 4**, `playtest_hostility.yml` (30 steps) **4 of 4**
(`output/studio_cal/xd02/a7/run/summary.out`, logs beside it).

**Pictures** (`output/studio_cal/xd02/a7/shots/`, `shots2/`, `shots3/`; sheets `sheet.jpg`, `sheet2.jpg`): the mess
hall's barrels with a clan pack before them (`shots3/01`), the shopping list's window (`shots/02`), the tally room
with its four guards and the timber table (`03`, `04`), the strongroom's carved roof (`06`), the Deep Line station, its
kegs and the note (`07`, `08`, `shots2/03`), the cart's locked line (`shots/10`), the cave-in line (`shots2/02`).

**Still blocked** (the move into the world, phase 0 item 3): the Mad Dwarf, Spider, Bat and Tiger Mole rows and the
brake key 12011 (A2); the quest bits 110020-110021 and Gunther's errand as a real quest (A3); `world: xeen`, music by
name and sounds (A1's install); the X4 exit (X4 not built).

## Into the world (2026-11-20, lane A7)

Phase 0 step 3, on the recipe of XD-05's move (lane lead). Files before: `output/studio_cal/xd02/a7_backup_move/`;
edits by `output/studio_cal/xd02/a7_move/move.py` (rows, items, relations, notes) and `a7_move/smithy.py` (the smithy
door), then `oymap fmt` and `oymap record --author agent:xeen-a7-move`.

- `world: xeen`. Slots by A2's slot names, tiers, counts and weights kept: 1 `Xeen Mad Dwarf` (Dif 0), 2 `Xeen Spider`
  (Dif 0), 3 `Xeen Bat` (Dif 1). The spawn points fix the tier: the three deep Dwarf points (`deep_station`,
  `stope_floor_n`, `turntable_n`) now at **b**, Clan Sergeant 11051 (10), as the Soldiers 10 they were; the four upper
  ones at a, Mad Dwarf 11050 (7); Spiders at a, Giant Spider 11320 (5); Bats at a, Giant Bat 11300 (3).
- Placed: the tally room's three guards Clan Sergeants 11051 (10); the fourth, once the Tallymaster, a Clan Guard
  11052 (12; CHANGES A1: an ordinary Clan Guard, one level over the band's top 10 as A2's row is); the four Tiger
  Moles 11430 (6, the row's own name: `name` dropped); the cocoon's three spiders Cave Spiders 11321 (10).
- Monsters at load (`output/studio_cal/a7/xcount.py xd02`, count.py reading the world's rows too): **about 56**
  (MAPS §0: 55), levels **3-12** (3-10 and the one Clan Guard).
- Items: `brake_key` 12011 (A2). The payroll amethyst 181, the lamp scroll 300 and the floor items (220, 222, 203, 825)
  are engine items and stay.
- `relations`: **all dropped**. They made MM7's Dwarves the party's foes and kept them apart from MM7's Spiders and
  Troglodytes; the world's `relations.yml` makes every Xeen family hostile and sets none on another. No peaceful
  actor stands in this map.
- Quest bits unchanged (110020-110021, A3's m3.yml), plus **`m3_done: 111061`** for the smithy below. A3's m3 hooks on
  this map (`winch`, `x4_adit`, `deep_line`, `dwarf_shop`) only name the built events and the bits they set or read;
  `xeen_quests.lua` defines no `m3.*` hook, so the map calls none.

**The Red Dwarf Smithy** (orchestrator's request from A4, `source/towns/xd02.yml` house 4851, TOWNS_FORMAT §1 `opens`):
`door:dwarf_smithy`, a wall panel of the area's plank door (`t3dr1`, the timbered theme's own door) 192 x 288 on the
adit mouth's south wall, between two timber sets, the first room past X1's portal (the party starts facing west with it
on the left). `evt:dwarf_smithy` (hover "Red Dwarf Smithy", a `script` with `condition: {qbit: m3_done}`): with M3 done
`evt.EnterHouse(4851)`; before, a message window with A4's closed text exactly ("The smithy is barred. Behind the
door, someone is sharpening something and swearing at the Mad Clan."). `playtest.yml` clicks it on arrival (the
window), sets 111061 by the console (`qbit set`), clicks again and asserts the house dialog "Red Dwarf Smithy" (the
world's house row 4851 loads), closes it and clears the bit. The audit's `click.silent` on it is its own blindness
to Lua (the EnterHouse).

**Dressing pass** (the user's rule of 2026-11-20, `devdocs/xeen/formats/DRESSING.md` "Measurements"; checker
`output/studio_cal/a7/dressing/check_dressing.py`, spots proposed by the lane's `output/studio_cal/a7/dressing/suggest_moves.py`
along the sector's real walls and off every walking line, edits `output/studio_cal/xd02/a7_dressing/batch1.py`,
`batch2.py`). Findings **25 -> 4** (`output/studio_cal/xd02/a7_dressing_before.txt`, `a7_dressing_after.txt`):
- moved to a wall or off the line: the adit mouth's two barrels (`adit_mouth_2`, `_3`, out of the portal's way to the
  north wall either side of the tipped cart); the Deep Line note's keg (`deep_station_100`, 300 from the line's mouth)
  to the brake wheel's side, still a stride from its empty partner; the lamp room's barrel; the mess hall's trash heap
  (out of the line between its two doors); the spider galleries' skeleton; the stope floor's dirt and rock (nudged 32
  and 48 off the walking line); the Top Station's third barrel (the clump of three made a pair and a single) and its
  bucket; the Turntable's two barrels (out of the trestle's doorway to its north wall, a pair) and trash heap;
- removed: the Top Station's two sacks on the loading deck (`top_station_17`, `_18`: on the deck between its openings,
  and every wall spot left would clump them with the barrels);
- kept, centre set pieces that narrow nothing: the mess hall's cook cauldron on its hearth (`mess_hall_58`) and the
  bowls, goblet and plates on the two long tables (`mess_hall_60`, `_62`, `_63`): the hearth and tables stand there as
  platforms, the things on them add nothing to the walk.


**After the pictures** (`output/studio_cal/xd02/a7_dressing/batch3.py`): the adit mouth's trash heap (`adit_mouth_4`)
stood against the Red Dwarf Smithy door's east jamb (the checker sees the smithy as a wall panel, not a door): moved to
the south wall's west bay, between the first two timber sets; the mess hall's trash heap, off the walking line but 230
from the west doorway, moved 330 off it (as a container would stand). The helper now keeps every prop 200 from a door
leaf, and with `STRICT=1` 330 from an open doorway.

## Sealed exits

The orchestrator's rule of 2026-11-20: no exit of a map in the Xeen world leads to an MM7 map. **The west adit to X4**
(X4, Burlock Savannah, is built in phase 2):
- **was:** project neighbour `exit:x4_adit` to `7out01.odm` (Emerald Island at [15816, 12161, 1133], direction 180,
  condition x4_adit_open, one way), the exit face `exit:x4` (sky_clo1, 320 x 352) on the collapsed adit's west wall with
  `evt:exit_x4` (an exit preset; locked text "Rock fills the adit to the roof. The winch might drag it away."), the
  plan's `entrance:west_adit`, and the winch's daylight (`light:west_daylight`, `lights_on`, "...: daylight!").
- **now:** the winch still drags the old fall away (mover:fall) and sets `x4_adit_open` (110020, A3's m3), and says
  "The props come out and the whole fall slides away, but behind it the rock has come down afresh." The adit ends at a
  rock panel of the fall's own rock (`panel:fresh_fall`, t3ll6, 320 x 352) where the sky face was; clicking it
  (`evt:exit_x4`, a script) shows before the winch the old status line and after it a message window: "Behind the old
  fall, fresh rock has come down and chokes the adit's mouth to the roof. No way out to the savannah here. Not yet."
  The built Lua has no MoveToMap but to X1 and XD-03. `playtest.yml` clicks it after the winch and checks the window
  and that the map is still XD-02.
- **to open it when X4 exists:** add back the neighbour `exit:x4_adit` (to X4's stem, arrival at X4's adit, direction,
  `condition: {qbit: x4_adit_open}`; drop `one_way` if it is two-way as M3 says), put back an `exits` entry on the
  collapsed adit's west wall (or turn `panel:fresh_fall` into it: same wall, centre, 320 x 352) with `to:
  exit:x4_adit`, make `evt:exit_x4` an exit preset again (condition x4_adit_open, the locked line above), restore the
  daylight light and the winch's line, the plan's `entrance:west_adit`, and a playtest step that takes it.
- **prepared (2026-11-20, lane A7, third session):** `output/studio_cal/a7/unseal_xd02_x4.py` makes every change above
  in one run once X4 is installed: neighbour `exit:x4_adit` to `xeen_x4.odm` at A5's arrival (20336, -16128, 1504)
  facing west (direction 180; X4's doorway face at x 20736, briefs/x4/DOORS.md), two-way, condition x4_adit_open; the
  exit face `exit:x4` (sky_clo1) in place of `panel:fresh_fall`; `evt:exit_x4` an exit preset; the daylight light and
  the winch's "daylight!" line back; the plan's `entrance:west_adit`; a load handler `evt:fall_cleared` that sends the
  fall away again whenever x4_adit_open is set (a map whose state was reset would otherwise put the rock back with the
  winch slack); `playtest.yml` no longer clicks the mouth, and a new `playtest_x4.yml` works the winch and leaves for
  X4. A dry run validated and built (MoveToMap (20336, -16128, 1504, 1024) to X4) and was put back. **The inside end:**
  A5's guess (2720, 5184, 256) stands inside the fall's footprint (x 2440-2776, y 4960-5408): the party would arrive in
  the rock if the fall were ever back; this map's arrival for X4's door:xd02_adit should be **(2880, 5120, 256) facing
  east** (direction 0), east of the fall's place and 180 clear of the winch (2920, 5300).

## Into the world: balance (2026-11-20, lane A7)

**Balance** (the orchestrator, 2026-11-20: kill XP per member within MAPS §0 ±15 %, by the tier mix first). Figures from `tools/xeen/balance.py --detail` (A2) and the lane's copy `output/studio_cal/a7/xbalance.py`, which skips objects.yml item spawns: A2's tool reads every indoor spawn entry as a monster marker of slot 1, item spawns included (a defect reported to A2; the lane's copy differs by that one filter). Reports: `output/studio_cal/a7/balance_before.txt`, `xbalance_before.txt`, `balance_after_tool.txt`, `xbalance_after.txt`; edits `output/studio_cal/a7/balance_move.py`. The slots' Dif, per_marker and weight are unchanged, so A2's map_stats row needs no copy.

| | Monsters | Kill XP per member (MAPS 1.1k) | Ratio, item spawns skipped | A2's tool |
|---|---|---|---|---|
| Before | 56 | 1.6k | 1.42 | 1.55 |
| After | 56 | 1.2k | **1.08** | 1.21 (the two item spawns read as 5 Mad Dwarves) |

- the three deep dwarf points (`deep_station`, `stope_floor_n`, `turntable_n`) back from b to a: every Dwarf point a Mad Dwarf 7 (the Clan Sergeant markers were the main excess);
- three of the open stope's spider points (`ledge_sse`, `ledge_wsw`, `foot_drift`) to slot 3 at a: bats over the stope's air instead of spiders (same count, half the XP);
- the tally room's three guards Clan Sergeants -> Mad Dwarves 11050 (the fourth stays the Clan Guard, CHANGES A1), the cocoon's three Cave Spiders 11321 -> Giant Spiders 11320.

Count unchanged (about 56), levels 3-12 (3-7 and the one Clan Guard 12). `playtest.yml`'s tally-room check now counts Mad Dwarves and the Clan Guard.

**Checks (final, 2026-11-20):** Studio checks against `output/studio_cal/a7/root_xeen` (its engine monster tables and, since this move, its engine items.txt carry the world's rows: `mk_studio_root.py`, then the lane's `mk_studio_root_items.py`, both write new files and rename); built into `output/studio_cal/xd02/a7_xbuild/`, installed with `oymap install --root assets_dev` and `--root output/studio_cal/a7/root_xgame`. Game checks with `build-xeen/game/openyamm --world xeen` from root_xgame (missing new world and engine files hard-linked into it with `cp -rl --update=none` twice during the move: a world.yml table, monster models; its X1 stand-in and XD-05 left as they were). `validate` no issues; `build` the three older warnings, plus the studio's
hostility warning for the three Xeen slots (engine `hostile.txt`, not the world's relations.yml: a studio defect);
`audit --reach --solve`: three hanging braziers' `thing.floating` (known), six sectors never reached (the bunk shelves
and chutes, by design), five steps, nothing stranded, exits to X1 and XD-03 only; `fmt --check` clean; playtests
**4 of 4**: `playtest.yml` 220 steps (the smithy barred and open, the sealed adit's window), `playtest_hostility.yml` 30
(`output/studio_cal/a7/final3_four.out`, logs `output/studio_cal/xd02/a7_xrun/`). Balance 1.08 (A2's tool 1.21: its
item-spawn defect). Pictures: `output/studio_cal/xd02/a7_xshots/` (sheet `a7_xshots_sheet.jpg`: the smithy door, the
tally guards, the drift, the barrel pairs, a Mad Dwarf and a Giant Spider at the Turntable) and `a7_xshots2/` (the smithy
door with the heap moved off it, the mess hall); looked at. Open: X4 (the sealed adit), A3's dwarf_shop question (the
house opens on m3.done 111061: whether Gunther's reward sets it is A3's).

## Lighting bake (2026-11-20, lane A7)

Profile `tools/lighting/baked_indoors/profiles/xeen_xd02.yml` (16 units per texel, one 2048-wide page, 128 samples, 3
bounces, light size 24; direct 2.0, bounce 5.0, ambient 0.9, ceiling 1.5: one calibration for the five, set on XD-05
against the unbaked map). Baked with `bake_indoor.py --game-binary build-xeen/game/openyamm --sources
output/studio_cal/xd05/a7_bake/xeen_sources` (Blender 5.3 in one process under a 16 GB cap; scripts in
`output/studio_cal/xd05/a7_bake/scripts/`, passes kept in `output/studio_cal/xd02/a7_bake/bake/` for `--recompose`).
`--sources` is a staged root of the world's own x4 masters (links to `level_generation/textures_xeen/finished/`): the
bake needs a material for every face and the Xeen textures have no source in `assets_source/worlds/xeen/textures_x4/`
yet. Installed `xeen_xd02.lighting` and `.bake.json` (new file, then rename).

- Bake: 2048 x 831 (1.70 M texels), 2,805 charts for 3,180 of 3,309 faces (242 mover faces), 56 static lights; 69 s
  Cycles, 75 s in all; `xeen_xd02.lighting` 3.65 MB, `.bake.json` 760 bytes.
- Pictures `output/studio_cal/xd02/a7_bake/` (`baked/`, `unbaked/` with `--set video.lightmaps=false`, `compare.jpg`
  baked left): 58.3 baked against 64.3 unbaked. Top station, mess hall, chapel and the stope floor match the unbaked map
  within a few percent, with shadows under the timber sets and pools round the lanterns; the gold pool and the grotto
  keep their colour. No black faces, seams or leaks seen.
- Switched lights (the bake keeps every BLV light as the map starts): The two signal lamps are BLV lights:
  `light:signal_trestle` (on at start) is baked and stays lit on the turntable's wall when the points are thrown;
  `light:signal_east` (off at start) never shows on the walls when it comes on (`turntable-points` pose: the baked map
  shows the green over the wrong gate). The six gold glints are pulsing lights: they go out correctly. The fix is the
  map's: build an event-switched light as a pulsing light (constant pulse) as INDOOR_PULSING_LIGHTS.md says, then
  re-bake.
- Stale check: listed only for the world's own x4 masters (`worlds/xeen/textures_x4/*.png`), which have no home in
  `assets_source` yet; with them in a source root at that path it lists nothing (checked), so installing the finished
  masters there byte for byte clears it without a re-bake.
- Playtest (`playtest.yml`, `assets_dev`, `--world xeen`): passed (`output/studio_cal/xd02/a7_bake/playtest.out`).
- Re-bake after any rebuild of the map: `output/studio_cal/xd05/a7_bake/scripts/bake_one.sh 2`, then `install.py 2`.

## Hooks, switched lights and D-7 dressing (2026-11-20, lane A7, second session)

**Switched lights as steady pulsing lights.** A bake keeps every BLV light as the map starts (INDOOR_BAKED_LIGHTING.md, INDOOR_PULSING_LIGHTS.md "Switched lights"), so each light an event switches is now a scene light with `pulse: {intensity: [1, 1], frequency: 0.1}` (constant): it is not baked, and `lights_on` / `lights_off` switch it as before (`evt.SetLight` key 40000 + its ids.lock number). Script: `output/studio_cal/a7/hooks/pulse_lights.py`. Here: `light:signal_trestle`, `light:signal_east`.

**Dressing (D-7.1, A1's recalibrated audit of 14:41).** `oymap audit --world xeen --reach --solve` on the installed map (scratch root `output/studio_cal/a7/root_d7`, lane script `output/studio_cal/a7/xcycle.sh`; walking-line pushes by `output/studio_cal/a7/dressing/fix_lines.py` and `d7_moves.py`): no error left. Changes: off the walking lines `main_drift_9`, `sorting_floor_29/30`, `west_line_76`, `west_line_upper_78` (rocks, heaps, dirt, 20-110 aside); removed `stope_floor_93` (a rock between the stope's lines), `sorting_floor_33` (a bucket 269 in front of a doorway) and `top_station_19` (a bucket on the line, no wall spot). The hanging braziers (`mess_hall_54/55`, `top_station_13`, `hangs: true`) reach their beams (the build's hang check is silent); the new audit no longer lists them.

### Dressing exceptions

- None: no dressing warning left.

## X4 linked (2026-11-20, lane A7, third session)

`output/studio_cal/a7/unseal_xd02_x4.py` applied (Sealed exits, "prepared"): the west adit leads to X4 at (20336,
-16128) facing west, measured **Z 1505** (A5's 1504); `playtest_x4.yml` (16 steps: shut, winch, leave via the
leave-map "OK"), `playtest` (216), `playtest_hostility` (30) every step 4 of 4 in `output/studio_cal/a7/root_x4`
(`output/studio_cal/a7/x4_four2.out`; the binary's exit crash as XD-07's); audit clean. Installed into `assets_dev`,
re-baked. X4's door:xd02_adit should arrive at (2880, 5120, 256) facing east, not (2720, 5184, 256), which stands in the
fall's footprint (asked of A5).

**A5's built X4 points (2026-11-20, later):** the exits now use A5's built arrivals (they supersede the provisional
DOORS.md ones above): XD-07 gate (-1024, 6912, 1808) south, throw (-4608, 9728, 2504) east; XD-25 (-11520, -9448, 1056)
south; XD-02 adit (20080, -16128, 1504) west; XD-26 mouth (-9216, 11208, 1824) south, sky crack (-7424, 14592, 3600)
south. Measured landing Z: 1802, 1505 (ground), 1057, 1505, 1821.5, 3593. Exit playtests 4 of 4 with clean exits in
`output/studio_cal/a7/root_x4` (`output/studio_cal/a7/x4_built_four.out`); installed, re-baked.

## Build warnings (2026-11-20, merge point 11)

Lane A7's warnings pass (oymap of merge point 11). Build warnings 1 → 0. Edited in the L4 YAML (the generators are
retired, above); before: `output/studio_cal/a7w/backup/xd02/`.

- "t3d2abe on BEAM is squashed (1 across, 0.41 down)": the trestle bents' ten X braces (16 wide, raking 66°: the plank
  picture's height is drawn out by 1/cos 66° along the brace). On a brace 16 wide it does not show (pictures from the
  chasm floor, before | after: `output/studio_cal/a7w/shots/xd02/sheet.jpg`), so the ten braces' surface says
  `uneven: true`; nothing else changed.
- Checks (root `output/studio_cal/a7w/root`): validate clean, build 0 warnings, audit `--reach --solve` no warning or
  error; `playtest.yml`, `playtest_hostility.yml`, `playtest_x4.yml` 4 of 4 each (`output/studio_cal/a7w/xd02_four.out`,
  logs `output/studio_cal/xd02/a7_xrun/`). The .blv is the same geometry; no re-bake needed for this change alone.

## Lamp rule (2026-11-20, lane A7, sixth session)

A1's light check (`oymap audit`, `devdocs/xeen/formats/LIGHTS.md`) found 15 errors and 4 warnings; now none
(root `output/studio_cal/a7/root_lights`, build `output/studio_cal/xd02/a7_xbuild`, 0 build warnings as before).
- The four `dec56` "pole torches" were the MM6 wall torch (bound `mount: wall`) standing on the floor: the chapel's pair
  (`dwarf_shrine_49`, `_50`) now hang on the south wall either side of the tablet, 144 up (level with its foot); the
  Turntable's pair by the points lever (`turntable_42`, `_43`) are standing flambeaux (`flamb00`) where they stood.
- Torches inside the timber props (`foot_drift_35`, `main_drift_6`, `main_drift_7`, `west_line_upper_77`: placed on the
  prop, they stood on its top) are now on the prop's open face, 12 off it, at their heights over the floor.
- In doorways: `mess_hall_56` moves along wall 0 from 0.85 to 0.92 (beside the Turntable door, 97 from its jamb);
  `stope_rim_83` from wall 3 (the gallery opening) to wall 2, along 0.6; `stope_floor_88` (the spiral's top ledge torch,
  on wall 1, the rim's mouth) to wall 0 along 0.75, height 928 (200 over the ramp's top there).
- `turntable_40` 73 from its wall: moved onto it at [7610, 4853].
- Not changed: `light:west_daylight` lies inside the rockfall plug that its event removes (switched off at the start).

## Texture fit (2026-11-20, merge point 16, lane A7, eighth session)

- The six ore carts' sides `xncartsd` (128 x 64) at `scale: 1.5` (a sloped side ignores `fit`): 1.04 x 0.92 of the picture on each 200 x 88 side, once.
- The tally room's four `xntally` boards 256 long (were 512: the board shown twice).
- AU's mine bed `xeen_amb_mine` placed twice (`sound:stope_mine` in the stope, `sound:sorting_mine` by the sorting floor; volume 0.45-0.5).
- Audit: no `textures.*` finding.

## Mine beds centred (2026-11-21, fifteenth session, lane A7 sub-agent)

- D-48 (AUDIO.md "Indoor beds"): `sound:sorting_mine` and `sound:stope_mine`, AU's `xeen_amb_mine` filling their
  rooms, take `pan: false` (heard centred, the falloff kept). No generator writes the sound lines
  (`tools/gen_objects.py` has none): edited in L4 `objects.yml` by hand.
- `xcycle.sh`: build warnings 0, audit 0 errors, 0 warnings. Installed with bake (01:55:33), stale bakes 0. From
  `assets_dev`, 4 of 4 each: `playtest` 216, `playtest_hostility` 30, `playtest_x4` 16
  (`output/studio_cal/a7/s15_xd02_four.out`).

## Twentieth session (2026-11-21, lane A7 lead)

- `exit:x1_adit` names X1's `entrance:xd02_portal` (-10240, 15872, 1184) facing south (A5 moved it in front of the portal; it was a raw point 400 south of the face, 259 from the named one; `direction` dropped, the facing comes with the name). `playtest.yml` asserts the landing and facing (measured (-10240, 15872, 1185) facing 1536).
- Built into `output/studio_cal/a7/s20/xd02/` with the oymap of merge point 27: BLV and scene byte for byte the installed ones (no rebake; stale bakes 0); the Lua differs by the way out only. Lua and studio file installed 06:51:18. Audit from `assets_dev` 0 errors, 0 warnings (`output/studio_cal/a7/s20/audit/xd02.txt`). **12/12 from `assets_dev`** (playtest 216, hostility 30, x4 16; `output/studio_cal/a7/s20/four_xd02.out`).

## Twenty-first session (2026-11-21, lane A7 lead)

- `exit:x4_adit` names X4's `entrance:xd02_adit` (19968, -15872, 1504) facing 1024 (west, out of the adit; A5 moved it;
  it was the raw point (20080, -16128, 1504) with `direction: 180`, now dropped). `playtest_x4.yml` asserts the landing
  and the facing. project.yml edited by hand (no generator writes it).
- Built with the oymap of merge point 27: BLV and scene byte for byte the installed ones (no rebake; stale bakes 0); the
  Lua differs by the X4 MoveToMap only. Lua and studio file installed 08:03:55. Audit from `assets_dev` 0 errors,
  0 warnings (`output/studio_cal/a7/s21/audit/xd02.txt`). **12/12 from `assets_dev`** (playtest 216, hostility 30, x4 16;
  `output/studio_cal/a7/s21/four_xd02.out`).

## Merge point 30 (2026-11-21, lane A7 twenty-third session)

- `panel:chalk_mark` stood over 112 of the strongroom's secret wall (merge point 30's panel warning: the sinking wall's
  top is 96, the mark's bottom was 64). Now bottom 296 (104 to 216, 8 above the wall's top) and offset 430, centred
  over the 192 of the wall. Edited in L4 `rooms.yml` by hand (`tools/gen_rooms.py` is stale since earlier hand edits).

## F14 drops (2026-11-22, lane A7 twenty-seventh session)

`tools/xeen/check_drops.py` (with A7 s27's blocks-on-floor fix) lists five pockets, all the trestle ride, kept by
design: the chasm floor under the trestle (-1792, reached only by stepping off the moving car; the gates at both ends
are down where the car stands, so nobody falls on foot) and four slivers of the car's own deck faces along its run
(the check does not ride movers). The car and its two levers carry the party both ways.

## chest.front (2026-11-22, lane A7 twenty-seventh session)

The build's `chest.front` warning (merge point 41: an indoor chest's `facing` is its long axis, its front 90 degrees
anticlockwise of it): the chest(s) it named turned 180 degrees in place, back to the wall, front to the room.
Installed with the bake; build warnings and audit as before.

## F43 (2026-11-24, agent xeen-fb3-dungeon): the chasm has a way out

The player fell off the trestle car into the chasm (z -1792) and could not get out: the F14 note above kept the chasm
"by design" because only the car reaches it, but a car is no way out. `ladder:chasm_north` (objects.yml) climbs the
chasm's north wall from its floor at (10912, 5616) to the foot drift (exit (10912, 5904), floor -192) through the gap
over the trestle. `check_drops.py`: 0 pockets (was 5). Still open: the east cart's gate and deck close through a party
standing in the gateway (sliding movers ignore bodies; studio request), and the winch's head and bars are not clicked.

## D-185 (2026-11-26, agent:xeen-fb5-dungeon2)

The three bunk niches' openings (`open:bunk_niche_1`-`3`, rooms.yml) 160 -> 192 high, the niches' full height: the Clan
Guard (h 181) presses into a 160-high frame when it chases the party into the bunk cut (F75). `check_monster_fit.py`
3 stuck -> 0. Audit 0 errors, `check_drops` 0, playtests 3 of 3 from the stage, installed and baked.
