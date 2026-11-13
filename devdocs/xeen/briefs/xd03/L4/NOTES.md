# XD-03 Deep Mine, L4: notes

A new dungeon built from the written brief (L1 to L3 here, `devdocs/xeen/MAPS.md` row XD-03, QUESTS.md Story M3,
MONSTERS_AND_ITEMS.md) with the Map Studio, by one agent, 2026-11-13, after XD-01's two passes and XD-02. No original
exists; shipped maps were measured and looked at for scale, light and texture families only (below).

State: `oymap validate` no issues, `fmt --check` clean. The build's warnings are the two placed monsters' names
(`Clan King`, `Gong Sentry`, gap 6) and the four placeholders (racks, gong model, cart model). 24 rooms, 24 sectors,
all reached on foot (`metrics --reach`: 24 of 24 with the doors open). Two playtests (175 and 46 steps) pass four runs
of four (`output/studio_cal/xd03/run/four.out`, logs `final_playtest_1..4.log`, `final_playtest_alarm_1..4.log`).

Scratch: `output/studio_cal/xd03/` (`go.sh` builds, installs into `mount/` and plays one test; `four.sh` the four runs
of both; `look.sh <tour>` builds, installs into the scratch root `root/` and takes a tour; `tour.yml` the pictures;
`ref/` the shipped maps looked at; `repro/`; `look1`-`look3`, `shots_take1`, `shots_take2` the earlier takes;
`tex/` texture sheets; `metrics.json`, `solve.txt`). Pictures: `output/studio_cal/xd03/shots/` (35 in the game, HUD off,
`captions.yml`, `plan.png`, `iso.png`).

**What was scripted.** The first shell, objects and wiring were written by two generators in my scratch folder,
`output/studio_cal/xd03/tools/gen_rooms.py` and `gen_objects.py` (the dome rings, the slag channel's lines, the gem
clusters, the cart's and cage's parts are computed), changed by the small `edit*.py` steps beside them and rerun after
each change; `regen.sh` runs them, `fmt` and `validate`. No hand edit has been made to rooms.yml, objects.yml or
wiring.yml that a rerun would lose; plan.yml, project.yml and the playtests are hand-written. Once the project is
edited by hand the generators must not be rerun.

## Shipped maps looked at first

`output/studio_cal/xd03/ref/`: MM7's Stone City `7d24` (the dwarves' city: plan, iso, metrics, 7 game pictures) and
MM6's Gharik's Forge `6d18` (lava forge: plan, iso, metrics, 7 pictures), plus the metrics of Snergle's Caverns `6d05`
(a dwarf king's caverns). What they taught, nothing of theirs copied:

- `7d24`: an octagonal great hall with dressed walls and timber frontages, dark floor, warm light high on the walls
  and a dark roof; tunnels of red rock between; 48.7 M units², 40 sectors, 3 loops, 3.86 light sources per M.
- `6d18`: the forge is one tall space over bright lava floors with dark rock and soot brick above; dressed tan halls
  (ctwl2/ctwl5, ctflor1) beside it; 56.6 M, 47 sectors, 2.93 light sources per M.
So: lava reads by its own light and should be the brightest thing in the hold; dark rock and soot above it; the dressed
stone of the King's own rooms warm and lit high; a hall wants its light in pools, not flat.

## Texture families (the lead's rule of 2026-11-13)

Every area takes its textures from one shipped map whose purpose fits; every texture was checked against
`output/studio_lead/blv_texture_use.json` (`output/studio_cal/xd03/tools/tex_report.py` lists each with the shipped
dungeons that use it; all 39 are used by at least one shipped dungeon, and by the family's own map):

| Area | Family (shipped map) | Textures |
|---|---|---|
| The mine: Deep Line head, landing, trestle, cart, sentry cut, lookout, breach, descent, escape shaft, the King's hoard, mole warren | MM7 `7d34` The Red Dwarf Mines (as XD-02, whose Deep Line this continues) | c2b, cfb1, c1gold (the hoard's gold-veined rock), tfb2, 7trimd, 7trimda, trim9_32a, trim11_32, ch004i (iron) |
| The clan's forge and hold: furnace hall, slag channel, bridges, gong gallery, back stair, barracks, lever alcove, armoury, furnace tower, antechamber, the King's hall | MM6 `6d18` Gharik's Forge | d2wlactr, vlcwl1lg, vlcwl1, vlcwl3a, vlcflorc, vlcflora, vlcflore, d2ceil1, d2ceil3, vlctrm3, ctwl5, ctwl5le, ctwl2, ctflor1, ctflor5, ctceil3, orfyrlga (the slag), vlcgnrc2, vlcgnrc3, bemh16a, bemv16a, bemvwal, d2lgdor |
| The geode grotto, its lower terrace, the crystal wall, the King's dome (the same geode, over the hall) | MM6 `6d05` Snergle's Caverns (a dwarf king's crystal caverns) | crstont, crdrf1, crflr3, d3ystlwl |
| The Red Dwarf vault (the old dwarves' work) | MM7 `7d24` Stone City | cwb, 7cdb, 7tfb1 |

Looked at as whole walls in the game (pictures in `shots/`): nothing shows a window, sign or emblem of another place.
Two stand-ins carry a motif chosen on purpose: the gong's face is `ctflor5` (gold scrollwork from the Forge's own
floor) and the throne's crest `ctceil3` (the Forge's red carved panel). The first take used textures from other
places (MM6 temple and hive crystal `orwtrlga` and `hvceila`, MM8 cave rock, an unshipped copper, rune and skull
texture); all were replaced. The geode's crystal-cavity panels (`d3ystlwl` on `crstont`) showed their brown frame as
pasted squares and were taken out; the cavity picture stays only on the singing crystal wall, where standing out is
the point.

Textures to generate (none shipped fits; the stand-in in use meanwhile):

| What it shows | Size | Where | Stand-in |
|---|---|---|---|
| A cold blue quartz lining: dark rock thick with pale blue crystal points | 256 x 256, tiling | geode walls and crown, the King's dome | `crstont` (blue-grey layered rock) |
| The same crystal cavity as `d3ystlwl` but in blue-grey rock (no brown border), for crystal faces in the geode walls | 256 x 256, single | geode wall panels, the singing wall | `d3ystlwl` on the door only |
| A bronze gong face: hammered bronze, a boss in the middle | 128 x 128 | the gong (six slabs) | `ctflor5` |
| The Mad Dwarf Clan's crest: a skull over an anvil, carved in red stone | 128 x 128 | the throne's crest | `ctceil3` |
| Glowing slag: dark cooled crust broken by orange-red seams | 256 x 256 | the channel and the gutters (brighter than the Forge's flat lava) | `orfyrlga` |

## The world it is built in

As XD-01 and XD-02: `world: xeen` validates but render, solve and the game refuse it, so L4 says `world: mm7`.

| Brief | Built as | Why |
|---|---|---|
| Slot 1 Mad Dwarves (Mad Dwarf 7, Clan Sergeant 12) | MM7 Dwarf family, tier 1 (Dwarven Soldier 10) | XD-02's stand-in; the only hostile-looking dwarf with an MM7 model. MM7 makes Dwarves the party's ally: a load event makes the three rows hostile (gap 2) |
| Slot 2 Spiders (10 / 14) | Spider family, tier 3 (Venomous Spider 8, Widowmaker 12); the spawns say `tier: b` and `c` | the same family |
| Slot 3 Burrowers (Tiger Mole 9) | Troglodyte family, tier 1 (Troglodyte Drone 9) | a level-9 burrower with a model (XD-02 placed the same) |
| Clan Sergeants (placed) | Dwarven Soldiers (229) | the Lieutenant (20) is far over 12 |
| The Clan King (18, three times the hit points) | Dwarven Lieutenant (230, level 20) with `hp: 300`, `name`, `immobile`, `carries` the key | the nearest dwarf in level; the game ignores the `hp` (100/100 in picture 27) |
| Bat Queens (10) | Inferno Bats (207, level 9), placed `hidden` | the Bat family's top rank |
| clan_king_key 12021 | Key to Snergle's Chambers (2108) | a dwarf king's key by name |
| qbits 110030-110031 | kept | the game sets and reads both (playtest) |
| music `cave_deep` | MM7 track 18 | the game refuses a name |
| XD-02 and X1 | Emerald Island `7out01.odm` at XD-01's point | neither is mounted with this map |

With a real Xeen world: `world: xeen`; the slots to Mad Dwarf 7 / Spider 10 / Tiger Mole 9, the sergeants and the
King to their own rows (the load event that makes the clan hostile goes; the King's hit points and his frenzy come
from his row and the world's `modifiers.yml`), the bats to Bat Queen 10, the key to 12021, music by name, the cart's
exit to XD-02's Deep Line station (XD-02 L4 about [4600, 4450, -1216]) and XD-02's `exit:deep_mine` arrival to this
map's Deep Line head ([8192, 1088, 384], facing west), the shaft to X1's shaft head, sounds from the Xeen audio
folder. The textures are the shared MM6-MM8 library and stay (with the five above generated).

## What the brief asks, and how each thing was built

L3's plan and coordinates are kept wherever they worked (the caves, the vault, the tower, the antechamber, the
barracks and armoury, the hoard and the shaft stand where L3 drew them); the departures are listed below.

- **The arrival by mine cart (a real ride).** The Deep Line comes in high in the landing's east wall: the party
  starts in the Deep Line head (a short rock-cut stretch with its rails, two timber sets and a torch) facing the mouth.
  On the mouth's ledge (a level 384 up) the cart waits at the top of the line's last pitch, a timber trestle of three
  bents under two stringers and iron rails falling 384 west to the floor. **Stepping onto the cart sends it down with
  the party on it** (a mover travelling [-768, 0, -384], a step event on its top) to the buffer stop, a baulk of timber
  on a stone, with a lantern over it; stepping onto it again at the bottom rides it back up, and the Deep Line's east
  end is the exit back to XD-02 ("always works from this end"). The cart is a plank wagon of parts (bed, front and side
  boards, four iron wheels). Pictures 01-04.
- **Sentry cut.** One path room with heights at its points: north, a jog, the long run past the lookout niche, then
  west and down 128 to the gallery door; three timber sets of dark posts and caps; torches in the niche and at the
  ramp's head. Pictures 05, 06.
- **The Furnace Hall** is one room now (L3: seven). 2560 x 2240, a rough rock roof 832 to 1216 over the floor on two
  soot-black timbers; dressed granite footing and soot brick to 448, raw dark volcanic rock above. The **slag channel**
  is a sunken level 128 deep and 384 wide at 45 degrees, its floor the Forge's lava (`floors: lava`: it burns), its
  sides glowing seamed rock. The **north span** (a slab 270 wide at the far bank, 611 at the near) covers its head; the
  **south bridge** (192 wide) crosses near its foot; both are hanging slabs flush with the banks, with a low iron kerb
  and no rail. The **slag steps** (four steps of 32, 352 wide) climb out of the main reach beside the south bridge; the
  **drain steps** (four, 224 wide) climb out of the south reach by the breach. The **ruined smelter** is an octagonal
  stack from floor to roof on a stone furnace base, its glowing mouth on the north face under an iron lintel; spoil
  heaps, buckets, slag lumps; four flambeaux with their own flickering light; six slag lights low over the channel
  pulsing out of step. Pictures 07, 10-14.
- **The gong gallery** is a balcony inside the hall, 384 up along its east wall behind a stone parapet (L3: a room
  beside the hall with two windows): its stair of twelve steps with side walls along the east wall at its south end,
  the gong at its north end, the sentry door from the cut in the middle, the back-stair head beside it. **The gong** is
  a round disc of six bronze slabs in a timber frame on a plinth (clicked). Picture 08.
- **The gong alarm (set:gong_alarm).** Coming onto the gallery marks the party as seen; a timer counts every two
  seconds while the sentry lives and the alarm is quiet, and at the third count (about six seconds) the sentry rings
  the gong. Killing him first keeps the barracks shut; the party can ring the gong itself. Either way the barracks'
  double door and the back-stair door fly open, the barracks' three torches light (switched lights over unlit torch
  models), a small camera shake (Lua). Both paths are played (`playtest_alarm.yml` lets the sentry ring).
- **Barracks**: plank ceiling on three beams, three bunk benches, a trestle table with benches, bowls and a goblet,
  barrels, unlit torches; five placed sergeants and dwarves asleep in the dark behind the doors; the lever alcove in
  the north wall (lever A, a torch). **Armoury** one step up through a plank door, its east wall folded into two bays
  with two weapon racks (rails on posts; the weapons are a placeholder), the clan's chest, an axe by the rack, a cask
  and a barrel. Pictures 15-18.
- **The King's Gate (set:kings_gate).** Two skull-studded leaves side by side with a mullion, each a hinged door; two
  iron bars across both (movers): lever A lifts the lower, lever B (in the furnace tower) the upper, each with a clank
  and visible from the antechamber; clicking the gate before both are up says "The gate is barred from within." and
  stays shut. The antechamber: a wedge under a pointed vault, the two hacked statues (clicked: "The clan has hacked his
  face away."), two flambeaux, two gate guards at their posts. Pictures 20-22.
- **Furnace tower**: L3's octagon with its roof drawing in to a sooty flue, a hearth of heat-cracked stone round the
  cold crucible (a cauldron with a slow red glow), two sconces, lever B on the west wall; stair of eight steps and a
  door. Picture 19.
- **The Clan King's hall.** L3's six-sided coffin shape widened to take its gutters, 2688 x 1792, 960 high: dressed
  tan blocks over a dark granite footing, a frieze of carved rune stone, carved pilasters in all six corners, four squat
  dressed pillars in a ring; a **dome of geode rock** in four rings rising to 1664 over the floor with the crystal
  cavity at its crown and a pale pulsing light in it; **the stepped dais** (six steps 1024 wide of granite risers and
  red inlay treads) to the throne floor along the north wall; **the anvil throne** (an anvil block that flares, on a
  plinth, with a high back and the clan's crest); the two forge braziers either side on stands, a skull pile and
  goblets; the hoard door behind it; six braziers round the walls; **two gutters** 32 deep along the east and west
  walls. Pictures 23-29.
- **The Clan King (set:clan_king).** Phase one: he stands on the throne floor (`immobile`) while his guard of four
  holds the foot of the dais. Phase two, when his guard has fallen (the brief: at half his health, gap 1): the forge
  braziers' fire lights go dark, a red light fills the hall, the gutters' beds turn to slag (`set_texture` on two
  platforms lying in the gutters) and burn whoever stands in them (step events that note the party in a gutter and a
  one-second timer that burns while the wrath holds, since a floor's lava flag cannot be set by an event), a camera
  shake. His death sets `clan_king_slain`; his key is in his corpse (`carries`).
- **The King's hoard**: gold-veined rock, a lantern, two trapped chests (450 gold, a ruby and three rolls of level 4;
  350 gold and four rolls), goblets, a fruit bowl; the shaft lever on its back wall beside the shaft. Picture 30.
- **The escape shaft (one way out until its lever is thrown).** A shaft 512 square going up 1856 beside a rock block
  whose top is the shaft head's landing (a level 1536 up), with the exit to the X1 hills on its east wall. **The
  counterweight cage is a mover that carries the party** up 1536 in ten seconds (iron frame, posts, a hanger bar and
  its chain as parts). Before the shaft lever the cage refuses ("its counterweight is chained fast") and so does the
  exit; the lever sets `escape_shaft_open`. Bell-pulls at the foot and at the head call the cage. Pictures 31, 32.
- **Geode grotto**: L3's breach, descent, upper terrace, steps and lower terrace; walls, crown and two columns of
  cold blue-grey crystal rock with rough walls and a roof rising to a crown 960 over the floor, a floor of dark crystal
  gravel, glowing crystals and crystal clusters (decorations) with slow blue pulsing lights, stalagmites, a skeleton
  and bones. **The bat queens hang hidden** in the crown and appear (`show_actors`) when the party steps onto the
  descent. **Four gem clusters** are tapering crystal points (platforms with ids): clicking one gives one low gem (zircon,
  iolite, citrine or amber) once, and its points are hidden and made passable. **The singing crystal wall** in the lower
  terrace's west wall is a secret door (`secret: true`) showing a crystal cavity; clicking it hums and sinks it.
  Pictures 33, 35.
- **Red Dwarf vault**: an octagon of Stone City's dressed stone over a footing of old blocks under a low dome, the
  memory crystal over a ring in the floor (a platform), the stone lectern (clicked: the mine's history as a message,
  noted in a map variable), the chest (amber, iolite, 150 gold, two rolls). Picture 36.
- **Mole warren**: the burrow mouth ramp and L3's knot of burrows round two rock cores, now with an uneven floor and a
  low uneven roof and rough walls, dark; tiger moles (two slot-3 spawns), the prospector's skeleton and bones, his pack
  (a chest: a potion, 100 gold, a roll) and a potion beside him. Picture 37.

Objects and wiring (every mechanism a preset with conditions and effects; Lua only for the clan's hostility on load
and the camera shakes):

| Brief | Built |
|---|---|
| Arrival and the cart back | `start` in the Deep Line head; `mover:deep_cart` with a step event (`toggles`); `exit:deep_cart` on the line's east end |
| Gong alarm | `evt:sentry_seen` (step on the gallery level), `evt:sentry_count` / `evt:sentry_rings` (timers, `kills` and `map_var` counts), `evt:gong` (the gong platform, `not alarm_rung`, `else_effects`) |
| King's Gate | `evt:lever_a` / `evt:lever_b` (switch, once, `opens` a bar, `sets`), `evt:gate_e` / `evt:gate_w` (door, `condition: all`, `action: open`, opens the other leaf) |
| Clan King | `evt:kings_wrath` (timer, once, `kills: group 4` and not the King), `evt:gutter_in` / `evt:gutter_out` (steps), `evt:gutter_burn` (timer), `evt:king_dead` (timer, once, `kills: monster`, qbit) |
| Hoard and shaft | `evt:door_hoard` (item, kept), `evt:shaft_lever` (switch, once, qbit), `evt:cage` / `evt:cage_call` / `evt:cage_call_top` (qbit), `evt:exit_x1` (qbit) |
| Geode | `evt:bats_drop` (step, once, `show_actors`), `evt:cluster_1..4` (script, once, `give_item one_of`, `hide`, `passable`), `evt:crystal_wall` (secret door), `evt:lectern` (message) |
| Doors | sentry (plank, hinged), barracks double door (two hinged leaves that open together), back stair, armoury, tower, gate, hoard, crystal wall: 10 doors and 4 movers |
| Chests | armoury (a field hammer, 60 gold, two rolls of 3), prospector's pack, Red Dwarf chest, the King's two (trapped, level 4) |
| Population | 9 monster spawn points (5 dwarf, 2 spider, 2 tiger mole) and 3 item spawn points; 18 placed: the King, his guard of 4, the gong sentry, 5 in the barracks, 3 on the far bank, 2 gate guards, 2 bat queens (hidden) |
| Lying items | a dwarven axe by the armoury's rack, a zircon in the geode, a potion by the prospector |
| Lights | 44 lights in objects.yml (26 pulsing: slag, flambeaux, the smelter's mouth, crucible, forge braziers, dome, geode, vault; 4 switched dark at the start: the barracks' three and the wrath's three) and 21 decorations that carry light |
| Decorations | 82: torches, lanterns, flambeaux, braziers, statues, barrels, cask, bowls, goblets, spoil heaps, buckets, rocks, crystals, stalagmites, skeletons, bones, the memory crystal |

## Scale against the bands

`oymap metrics <L4> --reach` (`output/studio_cal/xd03/metrics.json`); bands from
`devdocs/xeen/research/MAP_CRAFT_CALIBRATION.md` 3.1, 3.3 and 6.3.

| Figure | XD-03 L4 | Band |
|---|---|---|
| Floor area | 24.9 M units² (walkable 18.4) | S 20-35 (the brief's class); L3 measured 21.6 |
| Sectors | 24 | S 10-20, M 20-35; one sector per room (the hall, its channel, bridges and gallery are one) |
| Floor levels | -800 (warren) to +1216 (shaft head) walked; the hold at -512 and -128, the arrival +384 and 0, the caves -640 to -800 | 2-4; height range MM7 1,050-2,860, here 2,016 |
| Loops | 2: the barracks ring (gallery, back stair, barracks, hall) and the bridges inside the hall (metrics counts sector loops: 1) | at least 1 for M |
| Doors | 10 doors and 4 movers (14 door records); 17 door events | M 8-16, 5-14 door events |
| Monsters | about 35 (9 markers of 1-3 and 18 placed): 1.5 per sector | S 20-35; the brief about 34 |
| Chests | 5 (with the prospector's pack) | S 2-4, 3-7 |
| Secret faces | 2 (the crystal wall) | 1-6 per M dungeon |
| Plates, traps | no plates; 71 "pressure-plate" faces are the step events' floors (gallery, gutters, the hall's floor, the descent, the cart); harmful floors: the channel and the gutters | 1-15 plates |
| Boss | the Clan King (named, hit points ignored) | about 1 dungeon in 5 |
| Light sources | 39 counted by metrics (18 records, 21 decoration lights; the 26 pulsing lights are not counted): 1.57, really 2.6 per M units² | 7d24 3.86, 6d18 2.93, XD-02 2.0 |
| Decorations | 82, 3.3 per M | 7d24 2.77, 6d18 1.68 |
| Doorways | median 224 wide, 320 high | 256 x 256 |
| Sector height | median 640 (256 to 1856) | 464-592 mid rooms |
| Non-orthogonal rooms | 12 of 24 (the hall, the King's hall, landing, antechamber, armoury, tower, geode rooms, vault, warren, hoard); 13 with sloped, stepped, uneven or vaulted floors or roofs | at least 40 %, 25 % |
| Main wall texture | c2b 20 %, vlcwl3a 11 %, crstont 8 %, d2wlactr 8 % | one texture 45-85 % (here four families, one per area) |
| Clickable faces | 172 | 50-170 |

## Order of play (`oymap solve`, `output/studio_cal/xd03/solve.txt`)

```
step 0: 4 sectors   the Deep Line head and its ledge (the arrival)
step 1: 12 sectors  the cart (event 17) -> the landing; the gallery door (event 23) -> the cut, the hall and all open off it
step 2: 4 sectors   the barracks doors, the back stair, the geode (gem clusters, crystal wall)
step 3: 2 sectors   the armoury door; lever A (event 36) and lever B (event 37) -> the King's Gate (event 27) -> the King's hall
step 4: 2 sectors   needs item 2108 (the King's key): the hoard door -> the hoard and the shaft
step 5: needs qbit 110031 (the shaft lever): the cage -> the shaft head and the X1 exit
never reached: 0 sectors
```

That is the brief's critical path (landing, cut, gallery, hall, barracks, hall, tower, hall, antechamber, King's hall)
and return path (hall, hoard, shaft). `solve` does not see that the King carries the key (defect 2).

## Playtests

`playtest.yml` (175 steps): a level-9 party rides the cart down, walks the cut (lookouts), opens the gallery door and
kills the gong sentry at once (the alarm stays quiet ten seconds later), rings the gong itself (both barracks leaves
and the back-stair door open, the torches light, the gong refuses to ring twice), fights the sergeants, walks down the
gallery stair, through the barracks to lever A (the lower bar lifts), opens the armoury, loots its chest (the field
hammer) and picks up the axe; crosses the north span, fights the far bank's guard, finds the gate barred with one bar
up, climbs to the tower and throws lever B; walks into the slag of the main reach and out by the slag steps, over the
south bridge, into the south reach and out by the drain steps; through the breach and down the descent (the bat queens
appear), prises a gem cluster (one gem, once), sinks the crystal wall, reads the lectern and loots the Red Dwarf chest
(its amber and iolite); walks down to the mole warren and loots the prospector's pack (100 gold); opens the King's Gate,
kills the King's guard (the wrath: `kings_wrath` set), stands in the west gutter (it burns) and steps out (`in_gutter`
cleared), kills the King (`clan_king_slain`), takes the key from his corpse, opens the hoard (the key kept), loots the
King's first chest (its ruby), throws the shaft lever (`escape_shaft_open`), rides the cage to the shaft head and
leaves for the stand-in with both bits, the key and the ruby.

`playtest_alarm.yml` (46 steps): rides the cart down, steps off and on (it rides back up), off and on again (down);
walks the cut, opens the gallery door by its click and lets the sentry live: he rings the gong (`alarm_rung`, both
doors and the back-stair door open, the torches light); back through the cut, up on the cart, and out by the Deep Line.

Nothing depends on chance: only chests with fixed items are checked by those items; the gem is counted, not named;
the walks clear hostiles round the party, with small radii near the King. Two traps found while writing them:
`open_door` kills monsters near a door (it killed the sentry in the alarm test; that test clicks the door instead), and
`clear_hostiles` kills through walls (the hall's walks kept under the gallery's distance).

## Departures from the brief

1. **The gong gallery is a balcony inside the furnace hall** (the handoff's "the gallery over the hall"), not a room
   beside it with two windows; the overlook is the whole hall. Its stair runs inside the hall; L3's gallery stair and
   stair foot rooms are gone.
2. **The slag channel is one sunken level in one hall room** with hanging bridges (L3: seven rooms). A level must stay
   clear of the walls, so 32 of bank remain between the channel and the north and west walls; the channel's foot ends
   at the west wall instead of running under it.
3. **The drain is a flight of four steps** out of the south reach onto the bank by the breach, not a tunnel into the
   breach (an opening cannot sit below the hall's floor).
4. **The stepped dais and the throne floor are inside the King's hall** (a flight and a level along its north wall),
   not beyond a broad opening; the hall is widened to take the gutters (2688 x 1792, L3: 2304 x 1728).
5. **The King's second phase starts when his guard has fallen**, not at half his health (gap 1). The braziers' fire
   goes out by their lights; the brazier models cannot be swapped or tipped (gap 4). He leaves the dais only as far as
   `immobile` allows: the word cannot be lifted by an event, so he stays on the throne floor and fights from there.
6. **A door at the back stair's foot**, opened by the alarm: without it the sleeping sergeants would wander up the open
   stair long before any alarm.
7. **The arrival is the Deep Line's head** in the landing's east wall, 384 up, and the cart is a ride down a trestle
   (L3: the cart standing at the buffer stop on the landing's floor). The landing is 1536 x 896 (L3: 1024 x 768).
8. The north span and the south bridge have a low iron kerb (16) to read as bridges; still no rails.
9. **Texture families** instead of the brief's mixed picks (the lead's rule): the brief's `7tfb11` floors, `7cdb`
   hold, `d2flor`, `cwb1`/`cwb1gold`, `orwtrlga` geode, `vlcflord`, `MM7 lava` are replaced as the table above says.
10. The barracks has no bunk at its south-east corner (the back stair lands there); the armoury's racks are rails on
   posts with a placeholder for the weapons.

## Gaps (what I wanted to say and could not), most harmful first

1. **A condition on a monster's health** (set:clan_king, "phase two at half health"): `condition: {kills: {monster:
   monster:clan_king, hp_below: 0.5}}` or an actor script word (`monsters[].behaviour`). Used: the guard has fallen.
2. **A map's own monster relations** (XD-02's gap 1, unchanged): MM7's Dwarf rows are the party's allies; a load event's
   Lua `evt.SetMonsterRelation` makes them hostile. `project.yml relations` or `map_stats.slots[].hostile`.
3. **A placed monster's hit points, level and modifiers reach the game** (XD-01's gap, unchanged): the King has 100 hit
   points in the game (picture 27, `hp: 300` in the scene), no frenzy (`monsters[].modifiers: [frenzy]`), and
   `immobile` cannot be lifted by an event (an effect `mobile: monster:clan_king`).
4. **A decoration cannot be hidden, swapped or switched by an event**: the forge braziers cannot be kicked over
   (`brzier00` to `brazir2f`), the gem clusters had to be built of platforms to be hidden. `effects: {hide: deco:id}`,
   `{set_decoration: {of, to}}`.
5. **A floor's kind cannot be changed by an event**: the gutters burn by step events and a timer. `effects:
   {floor: {of: platform:gutter_w, kind: lava}}`.
6. **A placed monster's name shows only on its corpse** (`Clan King` shows as "Dwarven Lieutenant"): a project names
   table (XD-01's gap 2).
7. **Placed sounds of an MM7 project are refused** even for the engine's own sounds: `sounds[0].sound: the world mm7
   has no sound file lava loop` though `engine/audio/lava loop.wav` exists. The brief's slag bubbling, gong boom, crystal
   hum and wind in the shaft are missing. Repro `output/studio_cal/xd03/repro/sound_mm7/` (`validate.txt`).
8. **Exits only on walls**: the cart and the cage cannot be the way out; the party clicks the Deep Line's end and the
   shaft head's wall. `exits[]` on a mover or an effect `exit: <neighbour>`.
9. **No camera shake word** (the gong, the wrath, the shaft lever): Lua `evt.CameraShake`.
10. **No rotating lever**: the three levers are switch plates on walls.
11. **Things riding a mover**: the cart cannot carry a lantern or a decoration (`decorations[].rides`).
12. **Arrival points for the other entrances** (from X1 down the shaft) cannot be said in this project; only one `start`.

## Tool defects (repros under `output/studio_cal/xd03/repro/`)

1. **A platform on a raised level is measured from the room's floor, without a word.** A platform with `base` whose
   middle lies in a sunken level is measured from that level's floor (and the build says so); one on a raised level
   (a gallery, a dais) is measured from the room's floor and is built inside the level's solid block. The gong, its
   plinth and frame on the gallery and the whole throne on the dais were invisible in the first take; they now carry
   the level's height in their `base`. Repro `repro/platform_on_raised_level/` (`project/`, `result.txt`: the platform
   on the gallery at 384 has its top at 96, the one in the pit at -32).
2. **`solve` does not count an item a placed monster carries**: "item 2108 ... is not given or held in a chest on this
   map: it comes from elsewhere", though `monster:clan_king` `carries` it. Repro `repro/solve_carries/`.
3. **Placed sounds**: the refusal above names the world's audio folder only; the example it gives (`waterdrip.wav`) is
   not in that folder for MM7 (XD-01/XD-02's defect, unchanged). Repro `repro/sound_mm7/`.
4. **`oymap assets` hints mislead for some decorations**: `7dec11` ("dirt") draws as a dead tree, `Corpse` and
   `Corpse07` ("corpse") as standing living people in the game (first take, `shots_take1/37-mole-warren.png`); the
   skeleton is `dec05`, not `7dec05` (a cage) as the brief and the first lookup suggested.
5. The movers' schema text still says a level slide does not carry the party (XD-02's defect 3); the cart and cage
   here travel with a vertical part and carry.
6. Test harness: `open_door` kills monsters near the door (the gong sentry died to it); a light assertion on a pulsing
   light reads `unset`; in a screenshot tour the map's timers do not run (the wrath never fired however long a shot
   settled) and neither `actor kill <radius>` nor `lua evt.KillMapActor(...)` killed the King's guard, so pictures 28
   and 29 come from a scratch copy whose wrath event has no condition (`output/studio_cal/xd03/wrath_copy/`), run by
   the console's `event 34` (the playtest proves the real chain); a `walk_to` that ends while the party is still on a stair's steps reports a height
   between steps.
7. Minor: `plan.yml level` takes only L0-L3, so this L4's plan says `level: L3`.

## What in the brief was unclear

- "Phase two at half health" and "he comes down off the dais" have no words; the brief's state also lists him
  "frenzied" as a modifier the studio cannot give.
- The gutters are "dry until the second phase" but L3 draws them in the slag theme; a texture swap by event exists
  only for doors, platforms and panels (built so).
- The back stair is an open link; with sleeping sergeants behind closed hall doors it needs a door (built).
- The geode is "cold blue crystal" and the King's dome is "the geode's crystal": no shipped crystal texture is blue
  and coherent with a cave set; the nearest is Snergle's Caverns' blue-grey rock.
- "The bars are seen lifting from the antechamber" with bars across a gate whose leaves swing: built as bars in front
  of the leaves on the antechamber side, so the leaves swing into the hall.

## Pictures

Best: `shots/03-cart-riding-down.png` (the cart halfway down the trestle), `shots/07-gallery-overlook.png` (the hall
from the gong gallery: the smelter, the slag channel and the far bank), `shots/22-gate-opens-on-the-throne.png` (the
gate's leaves open on the throne at the far end), `shots/11-slag-channel.png` (the channel running across the hall
with the gong over it), `shots/16-barracks-alarm.png` with `15-barracks-asleep.png` (before and after the gong).
Also good: `08-gong.png`, `21-bars-lifted.png`, `23-king-hall-from-gate.png`, `29-gutter-burning.png` (from the picture copy), `33-geode.png`.
Weakest: `shots/24-dome.png` (the dome is a grey stone cupola with a small cavity at its crown, not the glittering
crystal the brief wants: the crystal texture to generate) and `shots/37-mole-warren.png` (a dark plain burrow).

Fixed after looking (takes `look1`-`look3`, `shots_take1`, `shots_take2`): the hall and the King's hall were flat and
bright (base darkness raised to 21-24, the light in pools); the gallery parapet hid the hall (lowered); the gong, its
frame and the whole throne were buried in their levels (defect 1); the dome and geode read as water and sky (other
families' crystal, replaced); the gate bars were pale (dark iron); the lanterns in the Deep Line head filled the
arrival picture (small torches); a dead tree and standing "corpses" in the warren and geode (skeletons and bones);
the armoury racks looked like doors (rails on posts); a tie beam in the tower drew as a spike up the flue (removed);
the geode's crystal-cavity panels looked pasted (removed); textures from the wrong places (the lead's rule).

## Judgement

As a dungeon it has what the brief promises and all of it works: you arrive on a real cart ride down the Deep Line's
last pitch, walk a timbered cut to a gallery where a sentry will ring the gong if you are slow, look down on a hall cut
by a glowing slag channel with two bridges and a ruined smelter, wake (or surprise) a barracks of sergeants, throw two
levers in two corners of the hold and watch the bars lift off the King's Gate, which opens on the throne at the far end
of a six-sided hall under a dome; the King's guard falls, the slag pours into the gutters, the King dies and leaves his
key, his hoard pays, and a counterweight cage carries you up a 1500-foot shaft to the hills. The optional geode has
bats that drop out of its crown, gems to prise out, a singing wall and an old vault. It is short and dense, as the
brief wants, and the alarm and the two-lever gate give the middle a plan to make.

Its weaknesses: the King's fight is an ordinary Dwarven Lieutenant with an ordinary 100 hit points who never leaves his
dais, and his second phase is a light change and two burning gutters, not a frenzied king; the dome does not glitter;
the furnace hall's walls are large plain planes of brick and granite under a dark roof; the geode is blue-grey rock
with crystal models rather than a crystal lining; the mole warren is a dark empty knot; there is no sound at all; the
clan are MM7's friendly dwarves made hostile by a line of Lua, all one model, so sergeants, guards and dwarves look
the same. A player would enjoy the cart, the gong, the two levers and the gate opening on the throne; the King himself
wants a Xeen row, an actor script and sounds before he is the climax the brief asks for.
