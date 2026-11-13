# XD-02 Red Dwarf Mines, L4: notes

A new dungeon built from the written brief (L1 to L3 here, `devdocs/xeen/MAPS.md` row XD-02, QUESTS.md Story M3,
MONSTERS_AND_ITEMS.md) with the Map Studio, by one agent, 2026-11-13, after XD-01's two passes. No original exists;
nothing was measured from a shipped map except scale, light and dressing (below).

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
