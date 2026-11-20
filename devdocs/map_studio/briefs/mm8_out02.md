# Brief: Ravenshore (MM8 `out02`, outdoor)

- **Levels:** L0 Pitch, L1 Plan (prose; YAML waits for the studio schema). **Date:** 2026-11-12. **Designer:** openyamm-fe.
- **Sources read:** CALIBRATION.md, PLAN.md §4; the out02 case study, Ravenshore catalogue and evidence JSON/PNGs; the
  out02 scene (entities, spawns, actors), ODM height/tile maps and map Lua; `map_stats`, `house_data`,
  `outdoor_travels`, transport and monster tables; the out02 census entry; the OUTDOOR, SETTLEMENT_DENSITY, HOUSE_VARIETY, WILDERNESS,
  LANDSCAPE_DETAIL and REGIONAL_TRANSITION calibration notes.
- **Conventions:** "the map" is the whole terrain square; "the playable square" is the area inside the edge-travel
  prompts (about the middle 70 % of each side). Positions are compass words and fractions of the map; north is up.

## L0 Pitch

Ravenshore is the merchant-ruled port at the heart of the continent and the party's home after the tutorial islands:
a crowded harbour town of dark-elf, human and ogre households where every road, ship and caravan of the region
meets. The town sits at sea level on the north-east shore of a wide bay, its market packed around a square
dominated by a huge glowing crystal, a raised temple on the point beyond, two ships at the piers and a poorer lane
village across the river mouth. Behind it a broad green basin, closed east and west by high upland walls and open
to the north along a winding river, holds wolf-haunted woods in the west and a centaur meadow in the north-east,
with six dungeon doors spread from the town square to a sea cave and a cliff-top chapel. It is played as a hub:
shop, train, bank and take quests in town, make short low-level forays into the basin, leave by three roads, two
ships or the guild caravans, and keep coming back; several doors stay shut until the story opens them. The mood is
busy, prosperous and safe in town, with a pleasant early-adventure countryside whose danger grows with distance.

## L1 Plan

### Identity and purpose

- **Role:** regional hub and respawn town (home and death-return point once visited); the main-quest council hall
  and the endgame portal are both on its square. Second map of the campaign, lowest band after the starter islands:
  treasure 1 of 6, trap and perception difficulty 1, refill about 2 years, rest-encounter chance 10 %.
- **Play pattern:** a service-dense town (nearly every service a short walk from the square), a wilderness ring of
  easy-to-medium fights, optional caches and stat bonuses, three road exits plus ships and caravans.

### Neighbours, travel and arrivals

| Way | Destination | Time | Arrival in this map | Approach character |
|---|---|---|---|---|
| North edge, on foot | Alvar | 5 days | North-centre, slightly west, beside the river | Open rolling grassland; road bends then runs long and straight to the edge |
| West edge, on foot | Garrote Gorge | 5 days | Inner end of the west pass, in the wolf woods | Narrow valley through the west uplands, staggered bends and projecting shoulders; the road stops a little short of the map edge |
| East edge, on foot | Shadowspire | 5 days | Inner end of the east pass, at the town's north-east back door | Deep rock cut with high flanks; screened, the destination is not visible |
| South edge (open sea) | listed as Shadowspire | 10 days | none | Not a real route; the whole south is sea |
| Captain's ship at the piers | Dagger Wound Islands; Regna | 5 days (2 days a week); 8 days (1 day a week) | On the pier | Arrivals from the islands also land here |
| Smuggler's ship at the piers | Ravage Roaming; Shadowspire | 4 days (2 days a week); 6 days (1 day a week) | On the pier | Second, shadier ship |
| Guild caravans (stable in the market) | Alvar; Shadowspire; Garrote Gorge | 2 days each, one or two days a week each | In front of the stable | Faster than walking |

The west and north arrivals are a short walk from the first wolves; the east arrival is a few minutes from the market.

### Landform

- **Sea and bay:** about a quarter of the map is water: open sea across the whole southern fifth to quarter, and a
  broad bay biting north into the south-west and south-centre almost to the map's middle. The town is on the bay's
  north-east shore; the east shore curves away south-east to the corner.
- **Basin:** the middle three-fifths of the width, bay to north edge: low and rolling, sea level at the coast to a few
  hundred units inland, gentle knolls to about 1,000–1,350 (one carries the buff pedestal). No cliffs inside it.
- **Uplands:** the outer fifth on each side, flat-topped at about 2,000–2,900, with steep rock faces down to the basin
  along their whole length; each cut to sea level by one pass (west: a little north of the middle; east: about the
  middle). Mostly backdrop beyond the travel prompts; only the inner rims are destinations (rim chests, chapel spur).
- **South-west headland:** highest ground (to about 6,400): a horseshoe of rock ridges joined to the west uplands,
  forming the bay's west arm and enclosing a small cliff-ringed sea inlet that opens south.
- **River:** enters the north edge just west of centre, runs south, swings east across the upper basin (upper
  bridge), meanders south-east, loops round and runs south-west into the bay's north-east corner, separating the west
  lanes from the market (town bridge). A small pond in the far north is backdrop.
- **Relief:** 0–6,400; the town is flat (sea-level market pads, lanes slightly raised, temple terrace about 640 up).

### Road graph (nodes and edges)

Nodes: N-edge, N-jct (north of the upper bridge), CW-jct (mid-basin, west of the river), W-jct (inner end of the west
pass), W-edge, Chapel, Lanes, T-bridge (river mouth), Square, Harbour, Temple, E-jct (north end of the market's east
street), E-edge, Oracle, Tomb.

| Edge | Purpose | Character |
|---|---|---|
| N-edge – N-jct | Main road from Alvar into the basin | Long, gently bent, follows the river's west side |
| N-jct – CW-jct (via upper bridge) | Spine of the countryside; links the north road to the west roads and the town | Crosses the river on the upper bridge, then runs south down the west bank |
| N-jct – Oracle – Tomb | Optional loop into the north-east meadow: seer, obelisk, tomb | Winding road east, then south-east to the foot of the east cliffs; dead end |
| W-edge – W-jct | Road from Garrote Gorge | Through the west pass, bends in the cut |
| W-jct – CW-jct | Joins the west arrival to the spine | Descends south-east through the wolf woods |
| W-jct – Chapel | Side road to the Chapel of Eep | Bends south then climbs onto an upland spur; dead end |
| CW-jct – Lanes – T-bridge | Road into town from the countryside | Follows the bay's north shore; becomes the single winding lane of the west lanes |
| T-bridge – Square | Town entrance from the west | Short; the crystal is straight ahead across the bridge |
| Square grid | Market streets | Orthogonal grid of about three by three blocks; one long east-west street on the north side, one north-south east street |
| East street: Square – E-jct | Market to the east pass and north-east houses | Straight north along the town's east side, passing the Might well and the vault |
| E-jct – E-edge | Road to Shadowspire | Through the east cut |
| East street south – Temple | Processional to the Sanctum | South from the market, rising onto the point |
| Square – Harbour | To the piers and fountain | Open plaza, no road surface |

Signposts at about four main junctions. No road reaches the den, the cove or the rim chests. Roads: about 4 % of land.

### Districts and zones

| Zone | Where | Share of map | Purpose | Density class |
|---|---|---|---|---|
| Market district | South-east of centre, on the bay's north-east shore, between the river mouth and the east uplands | about 1/20 | Square, services, rich and middle housing, guild hall | Dense market blocks: joined service blocks and houses forming streets and enclosed pockets; buildings cover about 30 % of the district; nearest-building gaps around 600 |
| Harbour | South-west edge of the market | small | Piers, two moored ships, crate stacks, fountain plaza | Open working waterfront |
| Temple point | South-east of the market, on the coast | small | The Sanctum on its terrace, with forecourt | Single landmark in open ground |
| West waterfront row | Between the town bridge and the harbour, on the market side | small | A handful of rich and middle houses, the stat-challenge garden | Loose row facing the bay |
| West lanes | Across the river mouth, west of the market, centred near the map's middle | about 1/40 | Poorer working village with the second tavern and the bad well | Village lane: small houses on both sides of one winding lane, short side gaps, refuse heaps and barrels in rear plots |
| Wolf woods | West half of the basin, from the west uplands to the river, north of the bay | about 1/6 | Low-level hunting ground, wolf den | Dense open woodland, with clearings and two camps |
| North-east meadow | East of the river, north of town, up to the east uplands | about 1/7 | Seer, obelisk, tomb, pedestal hill, centaurs | Open grassland with scattered trees and rocks |
| Uplands W and E | Outer fifth each side | about 1/3 together | Frame, passes, rim rewards, chapel | Mostly empty plateau and cliff |
| South-west headland | West arm of the bay | about 1/20 | Highest landmark; hides the smugglers' inlet | Bare rock |
| Sea and bay | South | about 1/4 | Travel by ship, sightlines, buoys | Water |

### Services and residences

- **Services (14 land destinations):** weapon shop 1, armour shop 1, magic shops 2, alchemist 1, elemental magic
  guild 1, self-magic guild 1, bank 1, temple 1, training hall 1, taverns 2, caravan stable 1, adventurers' inn
  (hirelings) 1. **Plus** 2 ships (captain; smuggler) and 1 seer (Oracle).
- **Grouping:** three joined service blocks round the square (north-west: weapons, elemental guild, both magic
  shops; north-east: training, tavern, alchemist; south-east: armour, bank, self guild, stable); free-standing inn
  (south of the square), temple (point), second tavern (west lanes), seer (meadow). The council hall exterior closes
  the square's south-west corner.
- **Residences:** 44 ordinary enterable houses in about 13 recurring forms (3–4 per form, a few rarer). About 22 in
  and around the market (middle and rich round the square and on the north fringe, a poor cluster in the south-east
  corner, one warehouse home), 17 in the west lanes (nearly all poor), 5 on the waterfront row (rich and middle, one
  warehouse home). Two are hostels (quest-NPC lodgings), one a bounty hunters' hall. Every door faces a shared
  street or lane; no private spurs. **Townsfolk:** about 45 peaceful residents and 20 guards, in town only.

### Points of interest

| POI | Count | Where | Behaviour |
|---|---|---|---|
| Crystal (endgame portal) | 1 | Centre of the square | Dungeon entrance, locked until the party holds the key built late in the story |
| Well, bonus | 1 | East edge of the market, off the east street | Temporary Might +25 once per active bonus, autonote |
| Well, harmful | 1 | West lanes, near the town bridge | "Not so refreshing": inflicts poison |
| Fountain | 1 | Harbour plaza, beside the council hall | Sets the town's Town Portal anchor; gives 200 gold, at most twice, when party plus bank gold is under 100 |
| Obelisk | 1 | North-east meadow, under the east cliffs, near the seer | One fragment of the continent's obelisk riddle, once |
| Buff pedestal | 1 | Top of a grassy knoll in the north-east meadow, among centaurs | Earth Resistance buff |
| Stat challenge | 1 | Garden on the west waterfront row, ringed by small stones, flowers and trees | Top tier: a character with a stat of 200 gains 10 skill points, once |
| Luck buoy | 1 of 4 buoys | In the bay, west of the harbour | Luck 20 or more: 5 skill points, once |
| Reagent spots | 2 | A tree north of the west lanes by the river; a rock on the pedestal knoll | Disarm skill 3 / 7: a random reagent / random stat potion, once |
| Sealed vault | 1 | North-east edge of the market | Opens with a late-story key item, then stays open |
| Locked prize chest | 1 | North end of the market | Opens only for the card-game champion award |
| Chests, free | 10 (+1 in a hollow tree) | 1 in a market back yard; wolf den mouth; a camp on a rise in the wolf woods; a three-chest cache at a camp in the north meadow; one beside the seer; three on the upland rims (north-west, east, north-east) | Ordinary loot; rim chests are reached off-road up the pass shoulders; the hollow tree is beside the upper bridge |
| Fires and camps | about 12 fires | Two wilderness camps (wolf woods rise; north meadow cache), a beacon on the west upland near the chapel, braziers by the temple, obelisk and chapel | Light and orientation |

### Dungeon entrances

| Entrance | Where | Purpose | Guarding |
|---|---|---|---|
| Council hall (merchant guild house) | South-west corner of the square, two doors (square side and harbour side) | Main-quest hub; first visit only talks at the door until the opening quest is done | None; in town |
| Crystal | Square centre | Endgame | Locked by key item |
| Dire Wolf Den | Foot of the west uplands' cliff, north-west wolf woods | Low-level lair; clearing every wolf on the map completes a local quest | Guarded: a wolf pack at the mouth, bones scattered, chest beside it |
| Smuggler's Cove | Sea cave inside the cliff-ringed inlet of the south-west headland | Optional smugglers' den | Deliberately quiet; no road and no land approach: reached over water (water walking or flight), so a later return |
| Chapel of Eep | Up on a spur of the west uplands, south of the west pass, by side road | Optional small chapel dungeon | Quiet; nearest wolves far off |
| Tomb of Lord Brinne | Foot of the north-east cliffs, end of the meadow loop road | Optional tomb | Centaurs roam the meadow nearby; no guard at the door |

### Encounter zones

| Zone | Slot | Monster and tiers | Packs | Where, relative to town |
|---|---|---|---|---|
| Wolf woods | C (third slot) | Dire wolves, difficulty 1, tiers A–C (about level 9–19), 1–3 per marker | About 10 tight packs of 3–5 markers (about 43 markers; ~85 wolves expected), packs ~4,000 apart with clear gaps | West half of the basin, from the west pass and den to the river and the central-west junction; nearest packs about 1/6 of the map from the lanes |
| North-east meadow | B (second slot) | Centaurs, difficulty 1, tiers A–C (about level 11–18), 1–3 per marker | About 16 single markers, loose, 1,000–2,000 apart | Between the river and the east uplands, around the pedestal knoll and the north meadow camp; none within about 1/10 of the map of the town's north fringe |
| Slot A | A | Human mercenaries, difficulty 3, 2–5 | none placed | Listed with zero weight; rest encounters split evenly between wolves and centaurs |
| Town, harbour, bay shore, south-west headland, uplands | none | — | — | Kept clear; cove and chapel approaches quiet on purpose. A story event can later fill the town with a hidden pirate force (about 80): a state, not baseline density |

### Landmarks and sightlines

- **Crystal** (tallest object in town): seen straight ahead from the town bridge and across the bay from the lanes.
- **Sanctum** towers on the south-east point: close the south end of the east street; seen from harbour and bay.
- **Two ships** at the piers ("this is the port"); **south-west headland**, the highest mass, framing the bay's west
  and hiding the cove; **upland walls** east and west with their two notches (the east cut screens Shadowspire).
- **Tomb** (large block monument) at the north-east cliff foot, seen down the meadow road; **seer's ring** (broad
  round stone platform) and **obelisk** in the north-east meadow.
- Key views: north arrival, the river leads the eye south to bay and skyline; harbour plaza, ships west and temple
  south-east; west lanes, across the river mouth to the market's towers.

### Deliberate open spaces

The crystal square (orientation centre, a few planted pockets); the harbour plaza (arrivals, fountain approach);
the temple forecourt; the seer's ring and pedestal knoll (focal points, no fight at the ring); clearings between
wolf packs; the open north-east meadow (long views); the bay (sightline space between lanes, town and headland).

### Bubble diagram (north up, not to scale)

```
                            [Alvar] N-edge
   W UPLANDS                    |  north road, west bank of river        E UPLANDS
   (rim chest)        hollow-tree chest                                   (rim chests)
                      (N-jct)=====loop road====[Seer ring]--[Obelisk]
   [Den]* bones          ||upper bridge          NE MEADOW: centaurs,
     WOLF WOODS         (river)                  pedestal knoll, 3-chest camp
 [Garrote]==W pass==(W-jct)  \                          [Tomb] at cliff foot
      |   camp+chest   \    (CW-jct)--reagent tree          river loops
  [Chapel] on spur      \___/     \                          \        (E-jct)==E cut==[Shadowspire]
                                   \__north-shore road__ WEST LANES ==T-bridge== MARKET  (vault, prize chest)
  SW HEADLAND (highest)                           (bad well, 2nd tavern)   [Crystal] square  (Might well)
   [Smuggler's Cove] in                  BAY (buoys)          council hall | 3 service blocks
   cliff-ringed inlet                                  HARBOUR: fountain, piers, 2 ships, inn
                                                                              [Sanctum] on the point
                                OPEN SEA (whole south)
```

## Designer notes

### Left for L2

Kits and tiers per district, the service blocks' and landmarks' compositions, the house list by form and tier,
bridges and piers; decoration palettes (close-planted market gardens holding most low plants, refuse and barrels in
the lanes' rear plots, dense west woods, scattered meadow trees and rocks, bare headland rock; about 15 lights);
fixed actor placement, chest contents, residents, quests; mechanisms (gate conditions, the pirate-invasion state, the
wolf-clearing check); atmosphere (clear temperate sky, plains music, harbour sounds).

### Brief gaps (candidates for the studio)

1. **Staged campaign states** (the invasion: hidden actor group, locked houses, bank emptied, kill-count end): PLAN
   §4 has "staged states", but the outdoor brief list does not ask for them.
2. **Gated POIs and entrances** (key item, quest step, award, skill or stat threshold, once-only, at most N times)
   need the shared Conditions vocabulary in the L1 tables, not prose.
3. **Reachability class** per destination (road, off-road, climb, water or flight only): the cove's lack of a land
   approach and the rim chests are intent a builder could easily break.
4. **Map flags:** home/respawn town, Town Portal anchor. **Travel:** playable square versus backdrop, arrival points
   with facing, the odd "south edge" entry, ship and caravan schedules (a world-level field).
5. **Encounter shape:** tight packs versus loose singles, markers versus actors, slot weights (a zero-weight slot),
   rest-encounter split; one density field cannot say it.
6. **Shared native rules:** stat challenge, obelisk and pedestal use world-wide state and global events; the brief
   needs "native shared rule" versus "local new rule".
7. **Physical versus logical counts:** one building with several services, one service with several doors (bank in
   three parts, council hall with two doors).
8. **Sightlines** need a from-where / to-what form for the evaluator's fixed cameras; **river course and required
   crossings** (which roads bridge which water) want their own field.

## Corrections from the L2 pass (2026-11-12)

The YAML briefs (`mm8_out02/L1`, `L2`) follow the original data where it differs from this prose:
- MM8 has no signpost decoration. The four "wayfinding" items are the bay's four buoys.
- The "braziers" are barrels. 14 fires are lit: two camp fires, two cook fires in the lanes, the chapel beacon, the challenge's fire basin and eight torches on the tomb.
- Only the square door of the council hall gives the talk before the opening quest; the harbour door always opens.
- The pirate invasion has 78 raiders.

## Corrections from the L3 pass (2026-11-12)

Measuring the original for the L3 sketch found errors in the prose above and in the L1 and L2 YAML. The YAML briefs
(`mm8_out02/L1`, `L2`, `L3`) now follow the measurement where it differs from this prose:
- **Heights.** The west lanes stand 128–192 up, not 256–512. The uplands are typically 2,200–2,500 but are not capped
  at 2,900: the west rises to about 3,700 and the east to about 3,100–3,300.
- **Arrivals.** The west arrival is on the pass road just inside the travel prompt, at the outer end of the west pass,
  well short of the west junction (about 18 cells in a straight line, nearer 28 along the winding road). The east
  arrival is in the east cut just inside the prompt, 7 cells out from the east junction.
- **North road.** It runs on the river's east side, about 10 cells off it, not along its west side.
- **Meadow road and obelisk.** The tomb road leaves the seer's ring southwards and never passes the obelisk. The
  obelisk stands off the road at the foot of the east cliffs, about 9 cells east of the ring.
- **Waterfront street (new link `road:waterfront_street`).** A town street runs from the south end of the town bridge
  along the waterfront row, down the council hall's west side to the fountain, and on to the harbour plaza.
- **Council hall doors.** The hall is L-shaped round a small yard that opens south-west onto the waterfront street
  where it meets the harbour plaza by the fountain. Both doors are reached from that yard and stand 256 up. The free
  door is at the hall's north-west corner, on a porch at the top of a short stair that climbs north from the yard.
  The quest-gated door is in the south face of the tower, on a walled terrace reached by a ramp. Neither door is on
  the square. The entrances are renamed `entrance:council_hall_porch` (free) and `entrance:council_hall_terrace`
  (gated).
- **Ships.** Both ships moor along the west pier, one on each side: the smuggler's to the north, the captain's to the
  south. The south pier has no ship. Each ship is about 5.4 cells long.
- **Building sizes** for whole assemblies, in cells east–west by north–south. Earlier sizes were often those of the
  largest part. North-west block 4.5 × 4, north-east block 3.9 × 3.75, south-east block 4 × 4.4, council hall
  4.6 × 4.1, Sanctum 5.25 × 6.25, Chapel of Eep 5.75 × 5, crystal 3 × 4, inn 3.75 × 2.9. Both bridges are about
  7 cells long.
- **Reagent tree and town bridge.** The reagent tree is about 17 cells east of the central-west junction, not near it.
  The town bridge crosses the river's last east–west stretch, about 5 cells before the river bends south for its last
  run of about 10 cells into the bay. It is not at the river mouth.
