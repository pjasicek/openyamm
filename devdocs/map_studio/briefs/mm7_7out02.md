# Brief: Harmondale (MM7 `7out02`), levels L0 and L1

- Map: Harmondale, world `mm7`, outdoor region (ODM) around Castle Harmondale, the party's own castle.
- Levels: L0 Pitch, L1 Plan (prose; the YAML form waits for the studio's `plan.yml` schema).
- Date: 2026-11-12. Designer: openyamm-fe.
- Sources read: `case_studies/outdoor/mm7_7out02.md`, `evidence/mm7/7out02.json`, `7out02_decorations.json` and the
  plan, height and decoration images; `7out02.odm` (BModel extents, height map and road-bank cells, via
  `util/map_export.py`); `7out02.scene.yml` (actors, spawns, entities) and `7out02_dimensional_travel.scene.yml`;
  `events/maps/7out02.lua`; GrayFace `mm7orig/txt/OUT02.txt` and `D21.txt`; `map_stats.txt`, `house_data.txt`,
  `outdoor_travels.txt`, `transport_locations.txt`, `trainer_places.txt`, `continent_settings.txt`,
  `monster_data.txt`; `outdoor_census.json` (7out02); `OUTDOOR_CALIBRATION.md`, `SETTLEMENT_DENSITY.md`.

## L0 Pitch

Harmondale is a contested border barony in temperate highlands, and the region the party is handed as its own: a
ruined castle on a shoulder at the head of a small, busy market town that sits in a sheltered bowl of hills. The town
is the party's home base for the whole game, with every everyday service, seven magic guilds and a stable, and it
stays safe ground. Beyond the bowl the land opens into a broad low basin of meadows held by goblins: an old hill fort
in the middle whose towers still throw fire, goblin bands roaming the basin, a quiet farming hamlet on the road
south, a small lake under white chalk cliffs that hide a goblin cave, and a lone tower in the east where the
kingdom's Arbiter sits in judgement. Play starts at the castle door: shop and train in town, clear the castle and the
basin, take the fort, light the three watch fires to bring the hidden raiding army out of the south-west hills, and
later restore the castle stage by stage while the region's politics (the Arbiter, the light-or-dark choice) play out
here. The mood is pastoral and homely inside the bowl, open and skirmishy outside it, with high bare hills and white
caps all round.

## L1 Plan

### Identity and purpose

- Role: the continent's home region and early-game hub. Starting map of the castle arc; the world's return point
  (respawn/home anchor at the castle forecourt) and a Town Portal destination.
- Profile: outdoor ODM, temperate highland, full 128-cell map. Map-stats character: low treasure and perception,
  encounters on rest rare (about 10%), refill roughly every two years of game time ("home town map, hills and
  scattered trees, water ok").
- Population tier: early game. One monster family in the wilds (goblins in three grades), plus a fixed band of
  mid-tier human swordsmen; town people are peasants and guards.

### Neighbours, travel and arrivals

| Exit | Leads to | Days | How | Arrival here |
|---|---|---|---|---|
| North edge, east of centre | The Tularean Forest | 5 | End of the high road through the north-east valley | Marker at the north road exit |
| West edge, a little south of mid-height | Erathia | 5 | End of the west road through a hill valley | Marker at the west road exit |
| South edge, just west of centre | The Barrow Downs | 5 | End of the south road | Marker at the south road exit |
| East edge | The Tularean Forest (its south side) | 7 | Off-road over the eastern rim; no road, no sign beyond a "East" hint | None (arrivals from the east use the north marker) |
| Stable (J.V.C. Corral) | Erathia, the Tularean Forest and one more region; the Arena | ~2 | Scheduled departures a few days a week | Stable yard (also where the Arena returns the party) |
| Castle door, cave mouth | Castle interior, White Cliff Caves | - | Dungeon entrances (below) | In front of each door |

- Party start: the castle forecourt, just east of the castle door, facing down the main street. No boats or docks.

### Landform

- A rim of high bare hills runs round all four edges (about the outer seventh of the map on each side), broken only
  by the three road valleys. Rim tops sit around the upper half of the height range; the highest knolls (to the map
  maximum, about 4,000) carry white chalk or snow caps, the largest a white massif in the south-east.
- Inside the rim the map has four parts:
  1. **Town bowl (north-west, inner)**: a sheltered pocket on low ground, closed by hills on the north, west and
     south and open only eastward to the basin. Inside it, three usable shelves: the main street on the floor, a
     guild terrace climbing north (up to about 650 above the street), a residential shelf on the south side (about
     640), and the castle shoulder at the west end (about 500).
  2. **Central basin**: the largest low, nearly flat ground, from the town's mouth east to the eastern rim and south
     to the lake. A few small rises inside it: the fort's mound, a small white knoll east of the fort, the Arbiter's
     knoll near the eastern rim (about 640).
  3. **South-west highlands**: a broad high block (about 1,500 to 3,200) between the west road and the south road,
     wooded on its slopes, with a ridge spur that separates the town bowl from the west road valley.
  4. **South-east lake country**: a chain of small lakes at basin level below the white cliffs, draining by a stream
     south-west to the south edge.
- Relief range 0 to about 4,000. Water about 1.5% of the map, white caps about 5 to 8%, road about 2% of land.
- Roads keep to valley floors; the west road winds through its hill valley rather than climbing over.

### Bubble diagram

```
            [N rim]========== north road ==========> N exit (Tularean, 5d)
               |                                 |   [N watch fire]   [Obelisk + crates]
  [W rim]  [TOWN BOWL]--- high road east --------+ NE valley ------- [NE spawns]
   orchard  castle > main street > town gate       \
   hill     (guilds N, homes S, market E)    junction  [CENTRAL BASIN]---- [Arbiter's knoll]
               | (ridge)                   (sign)  |   [HILL FORT]  white knoll       E rim (off-road
  [hermit huts on ridge]                   trunk S |       [shrine/altar]              exit, 7d)
 W exit <== west road == [SOUTH HAMLET] ==========+          [lake chain]
 (Erathia)  [W watch fire]   3-way sign  \ south road     long bridge -> [WHITE CLIFF CAVES]
  [SW HIGHLANDS: hidden raiding camp,     \ bridge over ravine    [SE white cliffs, spawns, chest]
   fruit trees, peak chest]                 > S exit (Barrow Downs, 5d) [S watch fire]
```

### Road graph

| Road | From → to | Purpose | Notes |
|---|---|---|---|
| Main street | Castle forecourt → town gate (east) | Spine of the town; every service fronts it or a short lane off it | Straight, on the bowl floor, about a fifth of the map wide |
| High road | Town gate → east across the north of the basin → bends north up the NE valley → north edge | Regional link to the Tularean Forest; longest road (about 40% of road length) | Passes north of the fort without touching it |
| Trunk | Junction just outside the town gate → south along the west side of the basin → south-west to the hamlet | Links town to the hamlet and the two southern exits | One signpost at its northern junction |
| West road | Hamlet → west through a winding hill valley → west edge | Link to Erathia | Watch fire on the hill beside its last stretch |
| South road | Hamlet → south-east then south along a valley → bridge over a ravine → south edge | Link to the Barrow Downs | Watch fire beside its last stretch |
| Town lanes | Two short spurs south off the main street | Reach the temple/training corner and the bank/stable/housing lane | |

- Junctions: three (town gate junction; the hamlet's three-way; the high road's bend into the NE valley) plus the
  two town spurs. No loops. Exits on roads: three.
- Deliberately off-road: the fort, the shrine, the Arbiter's hall, the obelisk, the cave (reached over a long
  footbridge across the lake outlet), the hermit huts, the orchard and every watch fire's hilltop approach.

### Districts and zones

| Zone | Purpose | Size class | Share of map | Density | Hostiles |
|---|---|---|---|---|---|
| Town bowl | Home town: services, guilds, homes, castle | Small town (about 24 x 24 plan cells incl. castle) | ~5% | Compact market core, village-street edges | None (safe) |
| Castle shoulder | Party's castle and start forecourt | Single landmark plot | <1% | One large assembly | None |
| Central basin | Open fighting ground; fort; shrine | Large | ~15% | Sparse trees and rocks | Random goblin packs; fort garrison; swordsmen band |
| NE valley | High road to the north exit; obelisk | Medium | ~10% | Sparse groves | Random goblin packs |
| East knoll | Arbiter's hall | Small | ~4% | Almost empty | Few |
| South hamlet | Farming hamlet at the road junction | Hamlet (4 houses) | ~2% | Open rural cluster | None |
| West road valley + ridge | Route west; hermit huts | Medium | ~6% | Light | None |
| SW highlands | Wooded heights; hidden raiding camp; fruit trees | Large | ~12% | Densest woodland on the map | Hidden army only |
| SE lake country | Lakes, white cliffs, goblin cave | Large | ~12% | Rocks, scattered trees | Random goblin packs |
| Outer rim | Frame and screen | - | ~35% | Bare, almost undecorated | None |

**Town composition.** The main street runs west to east along the bowl floor with the castle closing its west end.
East end (market): tavern, weapon and armour shops, bank, stable with its wagon yard, a well, the town entrance
facing the junction. Middle: magic shop and alchemist facing each other across the street, training hall, two long
planted flower beds in the street's middle (the town's garden). West-south-west (civic): temple with a tall spire,
town hall (a two-part assembly), training. North terraces (guild quarter): the seven guilds stepping up the slope,
Air highest at the top, Earth entered from a doorway in the slope at the foot, a fountain by the Water guild and a
well on the terrace. South shelf: eight home doors in seven houses (one house has two family doors), raised above
the street. Town actors: about 35 peasants and 5 guards walking the streets.

### Points of interest and behaviour

| POI | Count | Where | Behaviour |
|---|---|---|---|
| Wells | 3 | Town market (1), guild terrace (1), hamlet (1) | Market: gives a little gold once a week to a party that is nearly broke. Terrace: permanent small Accuracy gain, once per character. Hamlet: large temporary Might boost, resets daily, writes an autonote |
| Fountain | 1 | Guild terrace by the Water guild | Joke fountain: may cure a poison, otherwise warns the drinker off |
| Fruit trees | 8 | Four on the NW orchard hill above town, one in town, three in the SW highlands | Give an apple once, in spring and summer only; the tree then shows bare |
| Watch fire pits | 3 | One on a rise beside each road exit (N, W, S) | Clicking lights it (burnt-out to burning). All three lit: the hidden raiding camp in the SW highlands appears |
| Hill fort | 1 | Basin, just east of centre and a little north | Earth ring (about 10 cells across) round a square keep with four corner towers. The towers shoot fire spells at four approach sectors on a short timer, and when clicked. Stepping into the keep "takes" it once: four waves of about ten goblins arrive from the four sides, then the towers stop. Chest in the keep |
| Shrine with altar | 1 | South of the fort, north of the lakes | "You pray" until the party has visited the Land of the Giants; afterwards prayer teleports there |
| Obelisk | 1 | NE, near the high road's valley | Gives this region's letter of the continent's obelisk riddle, once, with an autonote |
| Arbiter's hall | 1 | East knoll | Round hall with a tower. House dialog for the Arbiter; three dialog variants depending on story state (see notes) |
| Chests and crates | 12 | Two crates by the obelisk; two wayside crates on the trunk; one crate in the hamlet; chest by the castle; chest in the fort keep; chest on the SE cliff top; chest on the highest SW peak; three crates in the stable yard | Ordinary loot containers |
| Hermit huts | 3 | High on the ridge between town and the west road | Two are residences, one is an inert hut |
| Signposts | 3 | Town gate junction, hamlet three-way, by the trunk | Hints naming destinations |

### Landmarks and sightlines

- **Castle Harmondale** on its shoulder closes the west end of the main street: seen head-on from the town gate and
  along the whole street. Ruined at the start, low and broken; it gains walls and towers as it is restored.
- **Temple spire**: the tallest structure in town, the town's skyline marker seen from the basin and the high road.
- **Hill fort**: its ring and four towers read clearly from the high road and the trunk; the towers' fire marks it
  as dangerous from afar.
- **White cliffs**: the bright massif behind the lakes, visible across the basin, draws the eye to the cave.
- **Arbiter's tower**: a lone upright on the east knoll, seen across the open basin.
- The bowl's hills screen the town from the basin (only castle and spire show before the gate); the rim hides each
  exit until the party is in its valley.

### Dungeon entrances

| Entrance | Dungeon | Purpose | How it is entered |
|---|---|---|---|
| Castle door (west end of town) | Castle Harmondale interior | Story: the party's castle, first full of monsters (rats, goblins, bats) | First click: the butler appears, gives the clean-out quest and moves to the tavern. Later clicks: into the castle as a dungeon. Once the castle is restored to its second stage, the same door opens the castle as a house dialog (throne room) on the interior map |
| Cave mouth in the white cliffs (SE) | White Cliff Caves | Optional early goblin cave (troglodytes, oozes) | Plain door; across the long footbridge over the lake outlet; returns the party to the cave mouth |

### Encounter zones

- Slot A only (goblin family, mixed grades, count 2 to 5 per pack). Slots B and C carry no random weight.
- About 43 spawn points (roughly 150 goblins expected), all east of the trunk: central basin around the fort
  (about 15), NE valley and north road (about 10), east and Arbiter's knoll (about 4), SE cliffs and cave approach
  (about 10), south lakeside and south road (about 4).
- Fixed groups: four hobgoblins in the fort keep; a band of about ten swordsmen (mid tier, above the goblins) camped
  round the fort's west and east sides.
- Hidden groups: the SW highlands raiding camp, about 75 goblins, hobgoblins and a goblin lord spread over the
  highlands down to the slopes above the hamlet, invisible until all three watch fires are lit; a squad of about 15
  (goblins, guards, adventurers) hidden in town that turns hostile when the guild-debt plot fails.
- Item spawns: three near the north exit, three on the SE white cliffs.
- Safe ground (no spawns): the town bowl, the castle, the hamlet, the west road valley, the SW highlands until the
  fires are lit.

### Deliberate open spaces

- Central basin: wide meadow for running fights and the fort's fields of fire; keep it mostly clear of trees.
- Castle forecourt: the start point and the view down the street.
- Stable yard and market end: wagons, crates and the well in an open yard at the town gate.
- Lake shores and the outer rim: bare, quiet ground that frames the map.

### Services and residences

- Services (17 doors): weapon, armour and magic shops, alchemist, tavern, bank, temple, training hall, town hall,
  stable; guilds Fire, Air, Spirit, Body (adept) and Water, Earth, Mind (initiate). No Light or Dark guild.
- Residences (15 doors): town 8 (7 houses), hamlet 5 (4 houses, one long house with two doors), ridge huts 2. Other
  houses: Castle Harmondale (dungeon or throne room) and the Arbiter's hall.

## Designer notes

### (a) Left for L2

Kits and palettes per zone and building tiers (town houses, guild forms, temple, castle stages, fort, hamlet, huts);
the exact building list with footprints, frontage and gap targets; decoration roles and counts per zone (about 290
trees, 230 flowers and plants, 40 rocks overall, densest in the SW highlands and in a ring round the town bowl;
planted beds in town); loose items (about 70) and chest contents; monster grades per pack and per fixed group; town
actor schedules; terrain tile banks and transitions; atmosphere (temperate sky, no fog or rain by default, the home
music track); lights (the three fires and a couple of town lights).

### (b) Brief gaps (things the L1 format could not express cleanly)

1. **Staged castle restoration.** The castle has at least three looks (ruined; repaired walls; upgraded towers),
   driven by story bits; geometry parts are shown or hidden and retextured, and two trees next to it change from dead
   to living. Needs staged states that swap BModel parts and decorations.
2. **Town lockdown state.** If the party fails the mercenary guild's deadline plot, every service and house door in
   town and the hamlet becomes "locked", the bank balance is wiped and the hidden town squad turns hostile; killing
   them (and clearing the castle) lifts it. A map-wide house-lock state plus a hidden-hostile group.
3. **Door that changes destination.** The castle door is a quest giver (first click), a dungeon entrance, then a
   house dialog on the same interior map. One entrance with conditional targets.
4. **House dialog with variants.** The Arbiter's hall shows one of three house variants by story state; a timed
   on-load messenger starts the succession quest, and NPCs move between houses here (judges, ambassadors).
5. **Hidden actor groups revealed by a condition** (three-of-three watch fires), distinct from spawn slots.
6. **Turret behaviour and capture.** The fort's towers fire at fixed target sectors on a timer until a one-shot
   "take the fort" trigger summons waves; the brief needs emitters, sectors and a capture rule.
7. **Conditional travel POI** (altar works only after the target map was visited).
8. **Well rules**: once per character, daily or weekly resets, a poverty condition. Fruit trees: seasonal yield and
   a sprite change after picking. Seasonal swaps of tree decorations across the map.
9. **World anchors**: home/respawn point, Town Portal destination, stable schedules and the Arena's return arrival,
   edge travel days with arrival-side mapping (the east edge arrives on another map's south side).
10. A later MAW overlay adds a dimensional-travel pedestal in the castle forecourt; it is not part of the original
    design and should stay an overlay project, not part of this brief's build.

Uncertain: the stable's third route (read as Tatalia from the transport rows) should be confirmed against the
world's stable table before L2.

## Corrections from the L2 pass (2026-11-12)

The YAML briefs (`mm7_7out02/L1`, `L2`) follow the original data where it differs from this prose:
- The joke fountain inflicts yellow poison, red poison or paralysis; it does not cure.
- One of the seven town houses stands north of the street, not on the residential shelf.
- Peasants: 25 in town and 7 in the hamlet.
- The stable's third route is confirmed as Tatalia (Monday, Wednesday, Friday).

## Corrections from the L3 pass (2026-11-12)

The L3 sketch measured the original's terrain, buildings and spawn points. Where they differ from this prose (and
from the earlier YAML), the YAML briefs (`mm7_7out02/L1`, `L2`, `L3`) now follow the measurement:
- Signposts: only two three-way signs (the town gate junction and the hamlet fork) plus the sign frame over the town
  entrance. There is no third sign by the trunk.
- Hermit huts: two on the ridge, both residences. There is no inert third hut.
- The magic shop and the alchemist stand side by side on the north side of the main street, facing the training hall
  and the bank across it. They do not face each other.
- Guild terrace levels: Body and Mind lowest (about 290), Fire and Spirit about 380, Water about 480, Air at the top
  (about 640); Earth's doorway is at street level at the foot.
- Residential shelf: only the double house and one manor stand on the shelf at about 640. The other four homes stand
  at street level along the south lane (the seventh town house is north of the market end).
- The main street is straight from the castle to the head of the south lane, then doglegs about three plan cells
  north and runs east through the gate.
- South road: it does not cross the lake outlet. From the hamlet it runs in its own cutting, about 640 deep, through
  a valley floor at about 640; the stone bridge spans that cutting, and the road passes under it. The outlet stream
  has its own ravine further east, which the cave's long footbridge crosses.
- Heights: the south road valley's floor, the Arbiter's shelf and a bare shelf at the east travel side all sit at
  about 640. The upper of the lakes lies on a shelf at about 400, not at basin level. The hamlet is low ground
  (about 0).
- Hill fort: the ring is a low built wall (about 128 high on a low terrace, its top about 256 above the basin), not an
  earth bank. Four of the basin's spawn points stand inside it, one by each tower.
- Encounter split (43 spawn points in all): round the fort about 22; on the basin's east side under the spire 4 (none
  on the Arbiter's knoll); round the high road's bend and the basin's north edge 9, only one of them up the north-east
  valley; at the lake outlet by the footbridge 3; on the white cliffs 5.
- Item spawns: the three placed "near the north exit" are on a white-capped knoll on the north rim, north of the gate
  junction.
- East edge: the off-road east exit is a bare shelf at about 640 between the north-east valley's walls and the hill
  north of the Arbiter's knoll. It is not reached over the rim.
- The rise east of the fort is not a small white knoll. It is a steep spire reaching about 3,200, with no white cap.
- The Arbiter's building is a small house (about 1.5 x 1 plan cells, with its roof ridge about 450 up) on a flat
  round base about 4 plan cells across. It is not a round hall with a tower.
- The cave's long footbridge belongs to the lake country with the cave mouth, not to the south road valley.
