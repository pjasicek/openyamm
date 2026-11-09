# How MM6–MM8 dress their dungeon rooms (study for the Hesper redress)

Read-only study of every MM6/MM7/MM8 BLV (161 maps, 4,968 sectors) plus engine captures of nine well-regarded
dungeons and of the lever/button mechanisms. Purpose: the Hesper dungeons need props that read as what they are. This
records what MM puts in a room, how much, where, and how it builds it. No Hesper file or game asset was changed.

## Contents

| Path | What |
|---|---|
| `scripts/analyse_blv.py` | Census of every BLV: `data/sectors.json` (per sector), `data/maps.csv`, `data/worlds.json` |
| `scripts/room_sizes.py` | Room footprints and size classes: `data/room_sizes.json`; `data/big_sectors.txt` lists every sector over 8 M |
| `scripts/mechanisms.py` | Levers, buttons, switches, lifts: clickable faces joined with their EVT Lua events and door records: `data/mechanisms.json` |
| `scripts/placement.py`, `scripts/extras.py` | Decoration placement (distance to walls, clustering), decoration roles, furniture textures (print only) |
| `scripts/tours.py`, `tour_picks.yml`, `tours/` | Camera placement from sector geometry and the engine screenshot tours |
| `scripts/contact_sheet.py`, `scripts/texture_sheet.py` | Contact sheets (tiles brightened, gamma 0.55 + auto-contrast) and the texture swatch sheet |
| `shots/<tour>/` | Raw 1600x900 engine captures |
| `sheets/` | `lincoln`, `control_center`, `hive`, `red_dwarf`, `snergle`, `wine_cellar`, `tidewater`, `harmondale`, `smugglers_cove`, `big_rooms`, `industrial` (forge and sewers), `mechanisms`, `textures.png` |

Captures are OpenYAMM's current renderer (x4 textures; some decorations and all monsters as 3D models), from a fresh
isolated save, so monsters stand in a few shots. A few auto-placed cameras face a wall (`snergle/sacks_s17`,
`smugglers_cove/cavern_s9`, `retake_big3/hall_s4_b`, several lever shots); the numbers and the other shots cover them.

Units: MM world units; areas in millions of square units (M u²). A 2,048 x 2,048 room is 4.2 M u². "Floor area" sums
every upward face of a sector (steps, platform and table tops included), so it is an upper bound on walkable area.
One sector is normally one room or one corridor run; MM does merge some caverns and mazes into one huge sector.

## 1. The numbers

### Per world

| World | Maps | Sectors with floor | Decorations | Per M u² floor | Median map | Sectors with no decoration | Maps with no decoration | Faces per M u² floor | Faces not in sector's 3 main textures |
|---|---|---|---|---|---|---|---|---|---|
| MM6 | 51 | 2,465 | 5,659 | 1.18 | 2.14 | 36 % | 1 | 18 | 44 % |
| MM7 | 63 | 1,570 | 3,278 | 0.70 | 0.79 | 59 % | 15 | 32 | 32 % |
| MM8 | 47 | 734 | 890 | 0.54 | 0.24 | 74 % | 22 | 53 | 32 % |

- **Decorations are mostly lights.** Light sources (torches, braziers, lanterns, chandeliers) are 81 % of MM6, 91 %
  of MM7 and 85 % of MM8 decorations. Only **9 % / 6 % / 3 %** of sectors hold any non-light prop decoration.
- Top decorations: MM6 `6torch01` 3,386, `trchb00` 754, then `smlbarel` (keg) 153, `bigbarel` 131, `bag_a` 123,
  `brnrock0` (burning rock) 106, `brazir2f` 92, `sklplrev` (skull pile) 86, `bag01`, `floursac` (sack) 67,
  `cauld00` (cauldron) 39, `corinth` (column) 32, crystals, `bucket`, `trasheap`, `bonecage`. MM7: `torch01` 1,846,
  `torch07` 644, `torch05` 244, `7dec32` (barrel) 208, then single digits: bones, goblets, trash heaps, statues,
  casks, fruit bowls. MM8: `dec56` (torch) 712, `dec29` (bones) 49, `dec03` (barrel) 47, chandeliers, lanterns.
- **Placement.** Lights sit on walls (median 8–12 units from a wall face; 94–99 % within 64). Prop decorations sit
  against walls or furniture: median 128 / 96 / 64 units from the nearest face of their sector; 59 / 69 / 75 % within
  160; only 9–19 % stand more than 400 units out. They cluster: in MM6 and MM8 48 % have another prop within 200
  units. A dressed sector has a median of **3 props (4 in MM8)**; the busiest MM6 storeroom has 63.
- **The real dressing is BLV geometry.** About a third of all faces (32–44 %) use a texture that is not one of the
  sector's three main surface textures: trims, door frames, chests, cabinets, beds, consoles, pipes, crates. Clickable
  faces (chests, doors, levers, panels): 4,725 MM6, 10,586 MM7, 5,052 MM8.

### The nine studied dungeons

| Map | World | Sectors | Floor M u² | Decorations (top) | Per M u² | Sectors w/o deco | BLV lights | Faces per M u² | Off-palette faces | Clickable faces |
|---|---|---|---|---|---|---|---|---|---|---|
| The Lincoln (7d23) | mm7 | 40 | 86.9 | 0 | 0 | 100 % | 267 | 45 | 34 % | 159 |
| Control Center (sci-fi) | mm6 | 87 | 178.1 | 0 | 0 | 100 % | 392 | 16 | 35 % | 180 |
| The Hive | mm6 | 79 | 98.4 | 2 (skull pile, keg) | 0.02 | 97 % | 28 | 41 | 21 % | 86 |
| Red Dwarf Mines (7d34) | mm7 | 53 | 100.5 | 261 (torch07 251, statue 6) | 2.6 | 11 % | 243 | 38 | 30 % | 621 |
| Snergle's Iron Mines (6d09) | mm6 | 59 | 40.7 | 62 (torch 18, sack 17, barrel 11) | 1.5 | 75 % | 23 | 53 | 55 % | 143 |
| Wine Cellar (7d16) | mm7 | 10 | 7.0 | 7 (torch 6, bones 1) | 1.0 | 80 % | 5 | 165 | 50 % | 118 |
| Tidewater Caverns (7d17) | mm7 | 12 | 74.8 | 75 (torch 64, barrel 5) | 1.0 | 25 % | 0 | 20 | 15 % | 74 |
| Castle Harmondale (7d29) | mm7 | 66 | 92.9 | 259 (torch 198, barrel 32, goblet 8) | 2.8 | 41 % | 19 | 51 | 29 % | 177 |
| Smuggler's Cove (d07) | mm8 | 16 | 87.9 | 21 (barrel dec03 21) | 0.24 | 81 % | 18 | 34 | 11 % | 154 |

**All three sci-fi maps use no decorations at all.** Every prop is BLV geometry with dedicated textures.

### Room sizes

Size classes per sector: corridor = mean width (floor area / long side) under 640 and long side at least 2.5 x that
width; otherwise small < 1 M, room 1–4 M, hall 4–8 M, huge >= 8 M u².

| World | Sector floor area p25 / p50 / p75 / p90 (M u²) | Over 2 M | Over 4 M | Over 8 M | Maps with an 8 M+ sector |
|---|---|---|---|---|---|
| MM6 | 0.26 / 0.51 / 1.18 / 2.58 | 340 (14 %) | 146 (6 %) | 75 (3 %) | 20 of 51 |
| MM7 | 0.52 / 1.26 / 2.76 / 5.88 | 532 (34 %) | 262 (17 %) | 109 (7 %) | 27 of 63 |
| MM8 | 0.63 / 1.19 / 2.32 / 4.16 | 220 (30 %) | 79 (11 %) | 29 (4 %) | 14 of 47 |

| Class (MM6 / MM7 / MM8) | Count | Median long x short side | Median height | Multi-level floors | Water/lava floor | Median free-standing wall faces | No decoration |
|---|---|---|---|---|---|---|---|
| Corridor | 1,145 / 370 / 186 | width p25–p75: 256–372 / 289–513 / 333–528 (median 272 / 452 / 423) | 272 / 512 / 512 | | | | |
| Small (< 1 M) | 793 / 423 / 191 | 768x512 / 768x512 / 832x640 | 256 / 416 / 400 | 21 / 43 / 45 % | 2 / 4 / 1 % | 0 | 38 / 71 / 69 % |
| Room (1–4 M) | 384 / 518 / 280 | 1792x1280 / 2048x1344 / 1864x1408 | 406 / 640 / 512 | 41 / 48 / 52 % | 9 / 7 / 9 % | 0 / 4 / 8 | 16 / 54 / 72 % |
| Hall (4–8 M) | 68 / 150 / 48 | 3712x2096 / 3280x2164 / 3188x2284 | 519 / 768 / 768 | 51 / 55 / 62 % | 9 / 11 / 6 % | 4 / 19 / 31 | 15 / 57 / 65 % |
| Huge (8 M+) | 75 / 109 / 29 | 6373x3840 / 4928x3328 / 5760x4224 | 1100 / 1280 / 1488 | 57 / 75 / 55 % | 12 / 30 / 0 % | 12 / 49 / 22 | 13 / 43 / 86 % |

"Free-standing wall faces" counts vertical faces at least 384 units inside the floor's bounding box: pillars,
partitions, machines and furniture standing in the room rather than against its walls.

**What the big rooms are for** (`data/big_sectors.txt` lists all 62 maps): the 8 M+ sectors are almost all
**boss lairs and arenas** (Wromthrax's Cave 221 M, Yaardrake's, Ilsingore's, the Dragon Caves, the three Arenas at
78 M), **set-piece naves and courts** (Tomb of VARN, Temple of Baa, Castle Darkmoor, Castle Gloaming, Watchtower 6,
Celeste, Temple of the Light), **natural caverns** (Tularean Caves, Tidewater, Smuggler's Cove, White Cliff Cave)
and **one-sector mazes** (Walls of Mist, The Maze). Ordinary rooms with a job are 1–4 M; a hall is 4–8 M. The sci-fi
maps follow the same rule: the Control Center's 42 M central hall and the Hive's 37 M reactor hall are the climax
rooms, and the Lincoln's largest sectors (11–14 M) are its two engine halls.

**How they are broken up.** More than half of the halls and big rooms have two or more floor levels; huge rooms
average dozens of free-standing faces. Seen in the captures:
- **Level changes and raised platforms:** the Lincoln's engine halls have raised console decks and an overhead
  mezzanine slab; Harmondale's 11 M hall (s33) has a round raised dais in the centre; the Control Center's central
  hall drops into sunken pits floored with a lit green grille (`swfloor2b` around `swflora` panels).
- **Fluid channels:** Gharik's Forge (s36, 8.9 M) is a lava channel down the room's middle with stone walkways on both
  sides and burning-crystal decorations (`brnrock0`) standing in the lava; Free Haven Sewer (s82, 27 M) and the
  Erathian Sewers (s30) are water halls with ledges and wall grates; Tidewater's 12 M hall is half water; the Hive's
  halls carry strips of blue fluid.
- **Pillar rows and partitions:** the Wine Cellar corridor is an arcade of square piers with torches; Red Dwarf's mine
  halls repeat timber portal frames (red-lit beams) along their length; Snergle's mine room stands
  timber posts (`cbeam5`) in a grid; Tidewater and Smuggler's Cove divide caverns with plank walls and crate stacks.
- **A centred set piece:** the Lincoln's reactor column (s32) on an octagonal glowing plinth, the Hive's reactor in a
  37 M hall, Harmondale's dais. One big object per big room, in the middle, everything else on the walls.
- **Genuinely empty big rooms exist but are caves:** Red Dwarf s51 (6.6 M, no decoration, two textures) is raw
  cavern; MM does not leave a built hall empty unless it is an arena.

## 2. Rules of thumb per room type

**Storage room / storeroom.** Size 1–3 M (Snergle s17 2.3x1.3 k, s38 2.3x1.3 k; Smuggler's s6/s7 2.1–2.5 k x
1.3–1.8 k; Control Center s34 3.4x1.2 k). Contents: one kind of stored thing, repeated, in **clusters against the
walls or in one corner**, never a uniform grid. MM6 uses decorations (17 `floursac` sacks + crate prisms `cb5top` /
`cb5side` in Snergle s17; `bigbarel` + `bag01` in s38: 12 decorations in two clumps). MM7/MM8 build the goods as
geometry: Smuggler's Cove stacks crates of three sizes (64, 128, 256; textures `crate_w64`, `cr_w128a/b`,
`cr_w256b`, some with painted shipping labels), two or three high, in piles of 4–8 with walkways between; the Red
Dwarf stores are wooden bins (`7t1cabs`, plain planks) with clickable lids. The Control Center's storeroom is a
long panelled hall with four clickable tech chests (`ch5*`, yellow ribbed crates) at its far end, nothing else.
Chests are always geometry: `ch1*`/`ch2*`/`ch3*`/`ch5*` textured boxes against a wall, clickable.

**Machine / industrial room.** MM builds machines from BLV prisms with dedicated textures and lets the room's function
show through **one big centred machine or a row of identical units, plus lines (pipes, cables, channels) that tie
them to the walls**. Examples: the Lincoln's reactor (s32: an octagonal column of `a1b`-type green-lit panelling on a
two-step octagonal plinth with a glowing rim, alone in a 4.6 M room); the Lincoln's engine hall (s37: rows of
U-shaped console pods, each an octagonal desk prism with a dished top and a dotted light-panel back, `sfw*`/`a*`
textures); the Control Center pipe room (s23: floor-to-ceiling pipe columns `swpipes`, steel and red, as thin
prisms against the walls; a frieze of lit wall units at head height; `swgirder` beams overhead); Gharik's Forge
(lava channel + walkways). Repetition is fine when the units are a functional row (console banks, pipe runs), never
as unrelated boxes. Nothing in these rooms is a plain cube: each machine part has a texture that says what it is.

**Hall.** 4–8 M, height 520–770, broken by level changes in more than half the cases and by pillars, a dais, a pit
or a fluid strip. Decorations are wall lights at even spacing (Red Dwarf: a torch on each portal post; Harmondale: a
row of sconces) plus, in MM6/MM7 castles, a few props by the walls (21–36 % of MM6 rooms and halls hold a prop decoration;
MM7/MM8 3–10 %). Sci-fi halls put console banks on the
long walls (the Lincoln s1: stacked green console units on both side walls, overhead slab) and leave the floor open.

**Corridor.** 256–512 wide (MM6 median 272, MM7/MM8 ~450), 256–512 high, and they carry **no props**: dressing is
the wall treatment (Control Center `swll4dk` panels with a ribbed ceiling; the Lincoln's green light strips at hand
height and on the ceiling), a carpet runner (Harmondale `s43`: 8,160 long, 544 wide, red runner, sconces), arches or
piers (Wine Cellar), or portal frames (Red Dwarf). Lights on the walls at regular spacing. Only 1–2 % of
corridors hold any non-light decoration.

**Office / quarters.** 0.3–1.5 M (Harmondale s49 1.4x0.9 k; Smuggler's s12 0.8x1.7 k; the Lincoln's four
identical 832x896 side rooms s23–s26). Furniture is geometry against the walls: beds as low boxes with a sheet or quilt
top (`7t1beds`, `t1beds2`, MM6 `qtextle1` quilt with `bd1rail` frame), tables and benches as simple slabs on legs
(MM8 `t1cabs` plank), a cabinet or shelf unit (`t1cabs`, `7t1cabs`), sometimes a painting texture on the wall and a
carpet texture on the floor (Harmondale). Two to four pieces, one of each kind. Bunkrooms repeat the bed.

**Library / archive.** Snergle s40, Harmondale s18 and s48, Wine Cellar s1: shelving units are tall prisms whose
front faces carry a shelf texture (`bookcas1`, `7t1books1`, MM8 `t1books`, wine bottles `7winerack`), set
**against the walls and in parallel freestanding rows forming aisles**, with one reading table near the centre and
a keg or bones on the floor. The texture does the work: rows of book spines read instantly even on a plain box.

**Shrine / altar room.** Centred altar or statue (decoration `7dec55`/`7dec54` statues, `ped01–06` pedestals,
`v6fount1` fountain, MM6 `corinth` columns flanking), wall lights, nothing else. MM uses events (`Altar of Might`,
pedestal statuette `SetSprite`) on the one centred object.

**Sci-fi maps specifically** (Lincoln, Control Center, Hive). Zero decorations; hundreds of BLV lights (267, 392);
the props are all geometry: console islands, wall console banks, a reactor column, pipe columns, girders, floor
grilles, wall map screens, tech chests. Wall textures themselves are busy machinery (`swll4dk`, `swankdk` rusty
panels; `sfw7a`, `sfw1b`, `a3b` ribbed metal; `a1b` green-lit tech panel), so even empty rooms read as machinery.
Interactive panels are single textured faces (`sfpnlon`/`sfpnloff` screen panels, `trekscrn` wall map,
`trekscon` console). The Hive swaps to organic hex textures (`hvwl*`, `hvflor*`) with fluid strips and one reactor.

**How varied?** One room type gets one dressing kit: Red Dwarf repeats the same timber frame and `torch07` 251
times, Harmondale repeats sconces, the Lincoln repeats one console pod. Variety comes from **each room having a
different job**: stores, beds, books, kitchen table with goblets and a fireplace (Harmondale s37), cells, a throne
dais. Within a room the repeated objects are the room's purpose (sacks in the sack room, crates in the crate room).

## 3. How MM builds big machines and furniture

- **Prisms with dedicated textures, not decorations.** Cabinets, beds, tables, bookcases, crates, chests, consoles,
  pipes and reactors are BLV faces of the room's own sector. Each object kind has its own texture, often a small
  tiling strip (`7t1cabs` planks, `7t1beds` sheet, `cr_w256b` crate side, `swpipes` pipe, `a1b` lit panel; see
  `sheets/textures.png`). Typical shapes: box (5 faces: the back is the wall), octagonal prism (pods, columns,
  plinths), stepped plinth (2–3 widening rings), thin tall prism (pipes, posts), slab on legs (tables).
- **Repeated units are copies of the same few-face shape** (console pods, cabins, crates in three sizes), stacked or
  rowed with walkways; the sector's main textures stay on walls and floor.
- **Glow is texture plus BLV light**, not a lamp decoration: the Lincoln's green strips and the Control Center's
  lit panels are emissive-looking textures with point lights nearby.
- Decorations are used for small loose items (sacks, kegs, barrels, bones, goblets, crystals, statues) and lights.

## 4. Interactive mechanisms

From `data/mechanisms.json`: 263 mechanism events (event titles Lever, Button, Switch, Lift, Elevator, Panel; untitled
click events such as the Lincoln's panels are not counted) whose clickable faces were found in the BLV.

| World | Mechanism events | Of which the clicked face is part of a moving BLV door | Move axis | Move length (median, p10–p90) | Static faces (texture swap or nothing) |
|---|---|---|---|---|---|
| MM6 | 105 | 99 | 59 vertical, 40 horizontal | 16 (16–32) | 6 |
| MM7 | 56 | 54 | 44 vertical, 10 horizontal | 32 (16–80) | 2 |
| MM8 | 102 | 87 | 36 vertical, 51 horizontal | 16 (16–64) | 15 |

- **A lever is a tiny BLV prism that is itself a door mechanism.** Its faces (median 5 clickable faces in MM6, 16
  in MM7, often a single face in MM8) belong to a door record
  (`scene.yml` `doors`: direction vector, `move_length`, speeds); clicking runs `evt.SetDoorState` on the lever's own
  door (it slides 16–32 units: the handle drops or the button sinks in) and on the door it operates. Lever textures
  are small strips of wood or metal (`bemh16a/b/c` MM6, `trim4_16a` and `trim5_32` MM7, `gn_mtl03` and `t1butts`
  MM8, `tws1f`). Examples: Gharik's Forge (6d18) levers, Barrow IV (mdk02) handle in a recessed wall slot,
  Balthazar Lair (d24) wall levers next to lettered stone tiles (`t31a01`) for a puzzle, Necromancers' Guild (d19).
- **A button** is a wall block in the wall's own texture (`twb1a` Breeding Zone and Wine Cellar, `7trimda`) that
  moves in, or a small plate (`hvtrim4` in the Hive, `t65b02` in MM8's Abandoned Temple).
- **Texture swaps** mark state on static faces: `t1swdd`→`t1swdu` (switch down/up icons, MM6 Goblinwatch), `d8s2on`,
  `t3s1off`/`t3s1on`, MM8 `t65b11b`→`t65b11c` (snake panel whose eye lights), the Lincoln's `sfpnloff`/`sfpnlon`
  screen panels and the Control Center's `trekscrn`/`trekscon`. `evt.SetTexture` appears 448 times across all maps.
- **MM never uses a decoration as a lever.** Decoration sprite swaps (`evt.SetSprite`, 325 calls) are for torches lit
  or put out, pedestal statuettes placed (`ped01–05`, `crysdisc`), picked fruit trees and hiding things.
- **Nothing rotates.** MM doors only translate along one vector; there are no wheels, valves or cranks that turn.
  A big mechanism is a door: lifts ("Lift", "Elevator": a floor slab moving vertically), sliding walls, bridges.

OpenYAMM today: BLV doors translate like MM's; decoration 3D models keep their events and switch model when an event
calls `SetSprite` to another bound decoration (`engine/models/indoor_decorations.yml`); models can `swing`
continuously or scroll UVs, and projectiles can `spin`, but no decoration model turns once on an event.
**A Hesper valve that turns when used needs a small engine addition** (a one-shot rotation of a decoration model,
or of a door's faces, about an axis, triggered by the event), or must fall back to a two-state model swap plus a
sound. Pair it, as MM pairs levers with doors, with something that visibly moves: a sluice gate or shutter as a
BLV door, and a gauge or status panel texture swap (the `sfpnloff`/`sfpnlon` pattern).

## 5. What this means for Hesper

General: give each room one job and dress it with that job's objects; build the big ones from BLV prisms with a
dedicated texture per object kind (no plain white cubes: a box with a texture that shows vents, labels, slots or
screens), put loose items in clusters of 3–8 against walls, keep corridors empty and lit by wall fixtures, and use
decorations mainly for lights and small loose items. Keep working rooms at 1–4 M u²; give any room over 4 M a
reason (the climax, a machine hall, a concourse) and break it with a level change, a channel, a pillar row or a
centred set piece.

**Pumping station, Pump Hall.** Model on the Lincoln reactor and engine halls plus Gharik's Forge:
- A row of 3–4 identical pump units down the hall (MM rows identical functional units): each a stack of prisms
  (an octagonal or 12-sided casing drum with a ribbed pump texture, a wider flange ring, a motor housing box with a
  vent/label texture on top, a stepped octagonal plinth), not a textured box or a slab.
- Pipes as thin octagonal prisms: verticals from each pump into the ceiling or wall, one horizontal manifold along a
  wall at 300–400 height, a dedicated pipe texture with flanges (the `swpipes` pattern, two colours for two fluids).
- A water channel (fluid floor) along one side or between the pumps, with walkways and a railing edge; a raised
  control gallery or mezzanine at one end with a console bank (wall console units, an `sfpnlon`-style status panel).
- Valves: handwheels on the manifold near each pump. Per section 4, a true turn needs the engine addition; the event
  should also open a BLV sluice door and swap a status-panel texture. Lights: wall fixtures plus glow textures.

**Airport terminal.**
- **Baggage / sorting halls:** conveyors as long low prisms (side texture with rollers, belt-top texture; MM's face
  flow attributes, used for water and lava, scroll a texture: check OpenYAMM's support before relying on it) running between wall openings with flap textures; sorting carousels as
  octagonal islands (the Lincoln pod shape) or a loop; baggage carts and bag piles as clusters of 3–8 by the belts
  and in one corner (Smuggler's crate piles: 2–3 sizes, stacked, labelled textures); chute openings on the wall.
  No row of identical white cubes: every box must be a recognisable kind (case, crate, cart, bin).
- **Concourse:** a long hall is fine when it is a concourse; break it with rows of seating islands and pillars at
  regular spacing, a raised gate podium at each gate, information screens as single textured wall faces at intervals
  (the `trekscrn` pattern), counters as a row of desk prisms along one wall, a floor runner texture down the middle.

**Colony archive.** The library pattern: tall shelf prisms with a dedicated rack texture (rows of data cartridges or
crystal slots with small lights, like `bookcas1` rows of spines) against the walls and in parallel freestanding
rows forming aisles 192–256 wide; one reading table or terminal desk centred (a `sfpnlon`-style screen face on it);
a few loose items at the row ends (the engine table already has `mcryst01` Memory Crystal and `crysdisc` Crystal
Disk decorations). Corridors between archive rooms: wall lights only.
