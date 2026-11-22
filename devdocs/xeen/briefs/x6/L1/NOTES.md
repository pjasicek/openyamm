# X6 Desert of the Sphinx: L1 plan (MU-3, MU-4) for the phase 4 review

A5, 2026-11-20. A plan only: there is no geometry. Nothing is built until a decider has approved the board. The three
YAML files here are written by `output/studio_cal/x6/tools/gen_l1.py`; edit the script, then run
`output/studio_cal/x6/tools/run.sh` (generate, `oymap fmt`, render, the census into `totals`, `oymap validate
--assets assets_dev`, the drawings and the board; the Python steps run under a cgroup memory cap). Validation: no
issues.

## What the plan holds

Source: Clouds A1 (north-west), B1 (north-east), A2 (south-west), B2 (south-east), pressed into the land inside the
rims. The rims are at x 24 (west, as X5's west rim) and y 24 (north, as X4's north rim), so the playable land is
x 24-109, y 24-109.

- **North-west: the Basenji heights (A1).**
  - Red-brown rock along the north rim, 2,350-2,750.
  - Castle Basenji (XD-14) stands on a crag at the cliff top with nothing but stars behind it.
  - A 1,100 cliff drops to the desert. A zigzag cliff path climbs from Arie's camp (4608, Q-C8) at its foot to the
    castle gate.
  - Along the cliff top: the Waters of Great Power, and the werewolves' den (a chest).
  - On the rock spit where the two rims meet: the Air Reflector (M37).
  - The Basenji cult's werewolves hold the heights.
- **North-east: the Desert of the Sphinx (B1).**
  - Dunes and red mesas (to 2,250).
  - The Northern Sphinx (XD-15) lies facing south at (82, 39). Between its paws are its door (q-c9.door) and the
    obelisks' sand mound (obelisks.cloud_hoard): one spot.
  - Chests: a wagon the dunes swallowed, a nest on a mesa top.
  - The obelisk stands on a red knoll by the Sphinx track.
  - The Gargoyle foothills fill the corner beyond the playable square.
  - Sand worms.
- **Middle: the pan and Sphinx Wells.**
  - The caravan road crosses a flat pan (1,250) from X4's edge (y 60) to the wells fork.
  - Sphinx Wells (A4's x6.yml) stands on the road: tavern 4301 and stables 4302 facing the road, homes 4303 and
    4304 across it, Old Ibb's well between them, a camel pen and palms.
  - West of the fork is the oasis: a pond (1,000, the map's lowest point and only water), palms and the oasis
    fountain (+2 Endurance, permanent).
  - The pan is quiet.
- **West: the rim dunes (A2).**
  - Dunes run to the west rim and pour over it, sand streaming off the lip (a particle gap, MU-2).
  - The Southern Sphinx (FD-02, sealed until Act VI) is buried to its shoulders at (35, 84).
  - Saul's hermitage and urn (4602) stand by the rim north of it; the Shrine of Energy is further north by the rim.
  - An explorer's pack (a chest) lies at the lip.
  - Sand worms.
- **South and south-east (B2).**
  - The steppe road runs south to X5 (x 50). Beside it are the Well of Accuracy and the South fork.
  - The rim track goes west to the Southern Sphinx. The coach lane goes east past the Summer Druid's grove (4601,
    Q-C1) and the sun stones to the Warzone coach yard.
  - The bone fields and the ruined caravanserai hold sand golems, and so do the dry downs toward X4.
  - The Barbaric Mountains rise to 3,700 inside the square. They hold sand golems and a prospector's camp (a
    chest).
- **The coach yard (D-8.1)** is a walled pocket, 6 x 6 cells, against the Barbaric cliffs at (83-89, 92-98).
  - It holds only Gorm's coach house (4305) and the arena gate (XD-20), which is cut in the cliff.
  - Its desert gate in the west wall is barred from inside until a party opens it from the desert side
    (x6.warzone_gate, 116100).
  - The yard is outside every encounter area. The nearest fight is 3,200 away.

## Figures (render_x6.py, `output/studio_cal/x6/mockups/figures.json`)

| Figure | Target | Plan |
| --- | --- | --- |
| Obelisk; device kinds | 1; >= 4, one permanent | 1 (red knoll by the Sphinx track, obelisks.x6); wells (Old Ibb's, Accuracy), fountains (oasis, Waters of Great Power), shrines (Energy, sun stones), cairn, urn, Reflector, hoard mound; permanent: oasis fountain (+2 Endurance), Shrine of Energy (+5 Air resistance) |
| POIs | MAPS 20-25; band used 20-30 | **28** by the D-20 census (chained within 400; service doors, gates and dungeon doors in; NPCs, residences, exits, landmarks out). Band 20-30: MAP_CRAFT 6.2's wilderness band (X6's role in maps.yml is wilderness). MAPS' 20-25 was counted before D-20 put service doors and gates in, and that adds the tavern, stables, coach house and the yard's gate (4 spots). See question 1 |
| POI spacing | 1,300-2,600 | nearest-neighbour median 5,300 (1,180-9,840); shipped deserts' median 4,390 (MAP_CRAFT 1.1) |
| Dungeon entrances | 3-6 | 4: XD-14 Basenji gate, XD-15 the Sphinx (amulet), XD-20 arena gate, FD-02 Southern Sphinx (Act VI); each sealed until its map exists |
| Outdoor chests | 4-10, a reason each | 7: swallowed wagon (worms), werewolves' den (the pack), ruined caravanserai (golems), bone-field pay chest (golems), explorer's rim pack (the lip), mesa nest (a climb), prospector's camp (golems in the mountains) |
| Spawn markers; hostiles at load | 45-70; 135 | 54; 135 (all on markers, groups 2-3; nothing placed) |
| Kill XP per member | 41.5k +-15 % | 42.1k (+1 %): sand worms 18.2k (Dif 2, mean level 33), werewolves 12.6k (Dif 4, mean 30), elemental golems 11.3k (Dif 2, mean 26) |
| Encounter areas (4,096²) | 3-8 of 6-30 | 6: Sphinx dunes 13.8, rim dunes 9.8, Basenji heights 6.7, dry downs 6.0, bone fields 7.0, Barbaric 6.5 |
| Quiet land | >= 1/3 | 56 % |
| First fight, map-edge arrivals | 2,000-6,000 | X4 road 2,300; X5 road 4,600 |
| Town arrivals (D-15) | town buffer 2,500 | Sphinx Wells 4,900 (doors 4,400); coach yard 3,800 (house and both gates 3,200); Arie 4,000, Saul 2,500, the Summer Druid 2,800 |
| Roads | 1-4 % | 1.7 % road (+ 1.9 % lanes) |
| Height range inside the playable box | >= 2,500 | **1,000-3,600 = 2,600** on the drawn land inside the square (oasis pond (40, 60) to the Barbaric peak (106, 103)); the sketch's points 1,080-3,700 inside it |
| 6,000 rule; wild land (D-11.5) | none over 6,000; <= 0.16 | farthest land 5,400 (at (79, 108)); 0.102 of the land over 3,000 from anything |
| Towns | compact | Sphinx Wells 9 x 8 cells, 4 buildings, 2 services: town_feel `--small` at L4 |
| Textures | outdoor cap 120 | kits: cloudside_town (plain grade, the hamlet and the yard walls), towers (Castle Basenji, grey rubble and black timber), MU-2's X6 ground (sand_ripples, sand_flat, rock_red, dirt_cracked, road_pebbles); the sphinxes from mm6 pyramid's egy walls at L3; no new textures named |

Census spots (28): the five entrance spots (the yard's desert gate, Basenji's gate, the Sphinx door together with the
hoard mound, the arena gate, FD-02); obelisk; Old Ibb's well; oasis fountain; Well of Accuracy; Shrine of Energy; sun
stones; caravan cairn; Waters of Great Power; Air Reflector; Saul's urn; 7 chests; 3 signposts; the tavern, stables
and coach house doors.

Monsters (A2's rows; all three exist):
- slot 1: Xeen Sand Worm, Dif 2, [2, 3]: Sand Worm 30, Armadillo 38, Great Worm 45.
- slot 2: Xeen Werewolf, Dif 4, [2, 3]: Wolfman 20, Werewolf 30, Greater Werewolf 40.
- slot 3: Xeen Elemental Golem, Dif 2, [2, 3]: Sand Golem 22, Water Golem 28, Cloud Golem 50. The Cloud Golem is
  the sheet's C 50.

No scorpions (question 2). The map_stats are in project.yml: 9104, continent 6, treasure 3, lock 8, trap 4, music 17,
desert.

## Choices

- **Edges:**
  - East, y 60: X4's west road (L4) reaches its x 0 at y 60 over a level span 54-66 at 1,150. X6 uses the same y,
    span and height. X4's other west spans continue here: the Gargoyle Range 24-50 at 2,400-3,200, then [50, 54],
    and the dry downs from 66.
  - South, x 50: X5's steppe road reaches its y 0 at x 50 over a level span 45-56 at 1,460. X6 uses the same x, span
    and height. X5's other north spans continue: the rim 0-24, stony rises 24-45, and the Frostspine and Ogre Hills'
    backs 56-128, which meet the Barbaric Mountains here.
  - Both neighbours seal their X6 edge today and open it when X6 is built.
- **Rims:** west at x 24 and north at y 24, so the cliff runs on unbroken from X5 and X4. The Air corner is the
  world's north-west corner.
- **The coach yard (D-8.1):** described above. Gorm's gate line is A4's `gate_line`. Route 430 waits for m7.sigil.
- **Moved from the source:**
  - The Northern Sphinx moves from B1's east side, (112, 28) at the source's scale, to (82, 39), so the X4 arrival
    sees it.
  - The Warzone gate moves from B2's far corner, (112, 108), to (88, 95), inside the playable square.
  - Castle Basenji, Arie, Saul, the Southern Sphinx and the Summer Druid stay in their source quadrants.
  - The Well of Accuracy is X5's (B3) in the source; MAPS puts it on X6.
- **Added generic devices** (needed for the 6,000 rule and the D-11.5 figure): the sun stones (south steppe), the
  caravan cairn (desert road), Old Ibb's well.
- **Saul's urn** is flavour only. Saul teaches Meditation by talk (A4), and the source's 10,000-gold urn mechanic is
  not carried over.
- **Kits:** see the textures row of the figures table.

## MU-4 concepts

Two `codex exec` calls (`tools/paint_x6.py`), one per view, no retries; both came back on the first attempt. The
results are `output/studio_cal/x6/mockups/raw/x6_arrival_v1.png` and `x6_signature_v1.png`, with prompts (.txt) and
logs (.log) beside them.

- **Arrival**, from X4's desert road at [106, 60], looking west-north-west. It shows the pebbled road over the
  cracked pan to Sphinx Wells' palms, awnings and camel pen, two red mesas with the obelisk on its knoll, the
  Northern Sphinx on the right, and Castle Basenji on a cliff. Against the plan:
  - A rim cliff with stars appears behind the Sphinx at the right edge. The plan has dunes and the Gargoyle foothills
    there; the north rim is about 18,000 away.
  - The castle stands much nearer and larger than planned. Planned, it is about 36,000 away on the north rim; painted,
    it sits on a mid-distance cliff that reads as a canyon wall.
  - The Sphinx is nearer than planned (about 16,000).
  - The road is wider than 3-4 m.
  - The sky has fair-weather clouds; the clear preset has fewer.
  - The dry downs on the left are a flat plain.
- **Signature**, from a dune crest at [38, 96], looking north-west along the west rim. It shows the dunes pouring
  over the lip in sand-falls with veils of sand streaming into the starfield, the Southern Sphinx buried to its
  shoulders facing east, Saul's stone hut with an awning and palms, and a castle on a cliff at the right edge. It
  follows the blockout. Against the plan:
  - Castle Basenji is painted in sandstone, not grey rubble and black timber, and much too near: it is about 33,000
    away.
  - Saul's hut stands beside the Sphinx. Planned, it is about 7,000 beyond it.
  - The low sun is in the west (late afternoon), which is right for the arid preset.
  - The sand-falls need a particle effect, which the studio does not have (MU-2's gap).

## Original lines (to wire at L4; A3's hooks and A4's flavour file)

- "Shrine of Energy.  Pray?" (`xeen/aaze0001:0`): the shrine's prompt.
- "The water is cool and refreshing." (`xeen/aaze0001:4`): Old Ibb's well and the Waters of Great Power.
- "Castle Basenji.  Enter?" (`xeen/aaze0001:19`): the gate window's meaning (D-24: the entrance preset).
- "Reflector. Activate?" / "The Reflector hums quietly." (`xeen/aaze0001:17-18`): A3's m37.reflector_air.
- "Enter the War Zone?" (`xeen/aaze0006:4`): the arena gate.
- Arie's and the Summer Druid's lines (`xeen/aaze0001:12-15`, `aaze0006:0-5`) are A3's quest topics. Saul's
  "Everyone should learn how to pray properly ..." (`xeen/aaze0002:1`) is A4's flavour topic.

## Quest hooks placed

- q-c9.door: the Sphinx door. obelisks.cloud_hoard: the mound between the paws. obelisks.x6: the obelisk.
- m37.reflector_air: the Air corner.
- x6.warzone_gate and x6.warzone_gate_open: the yard's desert gate, from each side.
- m40.sphinx_door: FD-02, phase 6.
- People outdoors: Arie 4608 (Q-C8), the Summer Druid 4601 (Q-C1), Saul 4602 (Meditation teacher).
- Doors: A4's `building:x6_tavern`, `building:x6_stables`, `building:x6_houses#1-2`, `building:warzone_coach`.
- Arrivals: `sphinx_wells` (also the Town Portal anchor) and `warzone_coach`.

## Open questions for the decider

1. **POI band.**
   - Options:
     - (a) Use 20-30 and keep 28.
     - (b) Cut to about 25 by taking the clicks off the sun stones, the caravan cairn and one signpost; the 6,000
       rule in the south steppe then needs a landmark (for example a standing rock) or a fight.
   - Evidence: MAPS' sheet says 20-25; MAP_CRAFT 6.2 gives desert 15-25 and wilderness 20-30; the D-20 census counts
     28; shipped deserts are Dragonsand 17, Ironsand 23, Bracada 24 (calibration counts). The spacing median of 5,300
     is above 1,300-2,600, against the shipped desert median of 4,390.
   - Depends on it: the L3 device list.
2. **Scorpions.** MAPS names "Scorpions (crawlers)", but the crawler row (Scorpion 16, Electrapede 20, Lava Roach 26)
   is under the A band 22-30.
   - Options:
     - (a) No scorpions on X6, as drawn.
     - (b) A2 makes an Act IV desert-scorpion row (about 26/34/42), which replaces the golems on the markers or
       shares their slot.
     - (c) A few placed crawlers as flavour, under the band.
   - Depends on it: the slots and A2's rows.
3. **Werewolves at Dif 4.**
   - Options:
     - (a) Keep Dif 4.
     - (b) Dif 3 (40.1k, half the pack at level 20).
   - Evidence: Dif 4 is 30 % Wolfman 20, 40 % Werewolf 30, 30 % Greater Werewolf 40, a mean level of 30. It keeps
     the pack in the band and the kill XP at 42.1k against 41.5k.
   - Depends on it: project.yml slot 2.
4. **The coach yard's place.**
   - Options:
     - (a) Against the Barbaric cliffs, as drawn. A coach party walks about 9,000 to Sphinx Wells after opening the
       gate.
     - (b) Beside Sphinx Wells, so coaches and caravans share one stop. The arena gate is then a built portal, not a
       cliff, and the hamlet's buffer must also cover the yard.
   - Depends on it: the south-east layout and the coach lane.
5. **Signature view.**
   - Options:
     - (a) The west rim's sand-falls with the Southern Sphinx, as painted; it follows WORLD_DESIGN's "X6 west".
     - (b) The Northern Sphinx with Castle Basenji on its cliff, which the arrival already shows.
   - Depends on it: L3's tour cameras and the sand-fall particles.
6. **Moved from the source.**
   - Options:
     - (a) Accept: the Northern Sphinx at (82, 39) in sight of the X4 road, the Warzone gate at (88, 95) inside the
       square.
     - (b) The Sphinx nearer its source place, (100, 32), at the Gargoyle foothills' foot. It would then be outside
       the arrival view.
   - Depends on it: the plan's north-east.
7. **The concepts' castle** (no change to the plan). Both paintings put Castle Basenji too near, and the signature
   paints it in sandstone. Confirm the plan's grey-rubble, black-timber castle (the towers kit) far on the north rim,
   for L3's art.

## Files

- Brief: `devdocs/xeen/briefs/x6/L1/{project,plan,sketch}.yml` (this folder).
- Scripts: `output/studio_cal/x6/tools/`:
  - `gen_l1.py`, the brief;
  - `render_x6.py`, the drawings, figures and census;
  - `paint_x6.py`, the Codex concepts;
  - `board_x6.py`, the board;
  - `run.sh`, the whole chain.
- Drawings: `output/studio_cal/x6/mockups/`:
  - `plan_x6.svg`, `plan_x6.png`, `plan_x6_2x.png`;
  - `blockout_arrival.png`, `blockout_signature.png`;
  - `board_x6.png`, `figures.json`;
  - the raw Codex returns in `raw/`.
