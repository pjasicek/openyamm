> Orchestrator note (2026-11-21): in ROWS and the A2 relay, "+16.9k Megadragon" is party XP; per member it is 4.2k (D-77, `reviews/D77_DECISION.md`).

# D7 and the planes P1–P4 L1: decisions (D-58)

> Orchestrator note (2026-11-21): D-5 (Alamar's hatch) is amended by D-61 Q14 (`devdocs/xeen/mockups/act5_a8_decisions.md`):
> before `m33.done` the hatch leads into DD-17; after it, into FD-01 Alamar Depths ("Castle Alamar is gone." until FD-01 installs).

Decider D-58, 2026-11-21. Where this file differs from `briefs/d7/L1/`, `briefs/p1/L1/` … `briefs/p4/L1/` (NOTES.md, plan.yml, project.yml, atmosphere.yml), the boards or `phase6/corners.yml`, this file wins.

**When L2 can start**
- D7's L2 can start once A6 has made the changes below and A2's row 9114 has landed (X8's lesson).
- Each plane's L2 can start once its map_stats row (9115–9118) and its element rows (change P-3) have landed.
- L4's walks from `assets_dev` also wait for:
  - A3's corner, toll, test and hazard hooks;
  - A4's doors;
  - S's sleeper, statues and pedestal (no stand-ins at L4).

**What was checked in the engine and the source**
- **Hidden placed actors.** An indoor actor with the Invisible attribute is not drawn (`IndoorGameView.cpp:1449`). The event runtime clears that bit by group, so guardians can be shown mid-visit. A1 only confirms, as D-56 relay 1 already asks.
- **Floor faces firing an event.** BLV faces with `PressurePlate` fire their event when stepped on (`IndoorWorldRuntime.cpp` 1357 and 4478). The hazard cells need no new engine work.
- **Burning lava.** An indoor floor face named `lavtyl` or `lava*` burns (`IndoorMovementController.cpp:1130`).
- **Water.** MM9's water volumes, with breath, drowning, a constant current per volume and swimmers, already run in open-air BLVs (MM9's outdoor maps are built that way; see `MM9_WATER_SWIMMING_DESIGN.md` Status). Two things are still open there:
  - a radial current;
  - Water Walk on a volume.
- **`Xeen.payGems`** exists and counts gem items.
- **`xeen_skyroads`** already exists in Xeen's `sky.yml`, under the alias `xeenroads`.
- **The source's Sky Lake sellers** (`aazex107`, `mazex107`) sell Fire, electricity, cold and Kinetic scarabs for 300, 300, 300 and 600 gems.
- **Q-D26's hoard piece** is the planned Wyrmfang 12530 (MONSTERS_AND_ITEMS §4.2), so it is not a new item.

---

## APPROVAL

### D7 The Skyroads: approved with changes (A6's default on 8 of 10 questions; Q5 and Q8 changed)

- **D-1 Spacing on the roads.**
  - Along the ring and the inner road, no stretch longer than 8,192 may pass without a group or a POI. Boards and quiet stops do not count.
  - Get there by moving the existing 19 groups and 35 road POIs, not by adding monsters.
  - The plan's largest nearest-neighbour gap, 13,096, must close to 8,192 or less.
  - L2's `measure.json` reports both figures.
- **D-2 The first castaway's island.**
  - Move it (and its rope bridge) so that the Megadragon's leash circle is at least **5,888** from every walkable place except the dragon road and the roost (D-54's rule). The island is now 4,326 away, inside the breath, with a T6 strongbox on it.
  - The rope bridge from the West Lookout stays, re-routed.
- **D-3 The Megadragon is unique.**
  - Killing it sets a Q-D26 qbit. The map's load event keeps it hidden after that, through refills and through a reset after a map rebuild.
- **D-4 Every one-way roof exit opens only after `m30.done`.**
  - Seven towers send parties up: DD-02, DD-03 stage 4, DD-05, DD-06, DD-07, DD-08 and DD-14.
  - DD-02 and DD-06 are level 14–30 dungeons, and D7 is level 50–75.
  - Before M30 each roof trapdoor reads "The trapdoor is shut fast." (A3).
  - The same gate already applies to the boats (D-5.3).
- **D-5 Alamar's hatch is opened from above.**
  - DD-17's side reads "Bolted from above." until the party has used the key on D7, which sets a qbit. After that it works both ways.
  - Nobody climbs out of Alamar into a living Megadragon.
- **D-6 Tolls.**
  - Paying a toll keeps it open until the map refills (a map variable). Nobody pays four tolls on every lap.
  - Refusing makes only that toll's two bandits hostile.
  - The source's 10,000 gold and its lines stay.
- **D-7 Boards.**
  - The 18 boards use P5's blank board face (and P5's REST STOP sign for the Rest Stops). Their text appears only on hover.
  - No lettered faces, and no new textures for the boards.
- **D-8 Concept corrections at L3 (the plan wins):**
  - Olympus is small at 25,600 and has no winged statue.
  - The Broken Launch is a plain marble jetty, not an arched bridge-head.
  - The roads are cloud with a paved band down the middle.
  - Olympus' gates are open gilded posts: no gate leaves, no griffin statues.
  - The temple stands on the square's north side, not on the gate's axis.
  - No carved kerbs and no planting.

### P1 Plane of Fire: approved with changes

- **P-1 (all four planes) The test is recorded in a qbit, not a map variable.**
  - Use qbits **111764–111767**, one per element.
  - A map variable is lost on a refill and on the reset after a map rebuild (Saved map states). That would close the gate on a party that has already passed.
  - The load event reads the qbit:
    - the gate stays open;
    - the guardians stay hidden;
    - the pit stays quiet.
- **P-2 (all four) No bypass of the test.**
  - L2 proves that the sleeper's hall or chamber, its chest and the dais cannot be reached except through the gate:
    - not from the lava, the scree or the water;
    - not by any drop.
  - Every wall or lip on those approaches stands at least 192 above whatever touches it.
- **P-3 (all four) The rows follow C6 as decided below** (nine new rows, plus new names for the Fire family).
- **P-4 Concept corrections at L3:**
  - The crater wall is ragged cliffs, not cut slabs.
  - The statue stands about 3,700 away, not nearer.
  - The Crucible stands on its rise.

### P2 Plane of Air: approved with changes

- P-1, P-2 and P-3 apply.
- **Concept corrections at L3:**
  - The aerie is the highest island (768).
  - No posts or pennants on the walking line. L3 dressing may put them at the edges only.
  - The statue's plinth stands in the middle of its island.

### P3 Plane of Earth: approved with changes

- P-1, P-2 and P-3 apply.
- **Concept corrections at L3:**
  - The bowl must read deep: the scree 1,024 under the arrival, the Hollow 768.
  - The walls lean in like a cavern's, not as quarried steps.
  - The Pillar Field is rough pillars like petrified trees.

### P4 Plane of Water: approved with changes

- P-1, P-2 and P-3 apply.
- **Currents.** The outer sea's push-back is built from edge volumes, each with a constant inward `current` of 256. The radial current is still open engine work and is not used.
- **Octopods.** They are placed with homes at least 1,024 from the arrival terrace, the test's court and the Grotto. They may threaten the walks from the water; that is intended.
- **Concept corrections at L3:**
  - The sky is an open sky (Q3), not an underwater ceiling.
  - The Grotto is at the plan's scale.
  - The statue stands in the middle of its forecourt.

---

## ANSWERS: D7

**Q1 The size of the ring**
- **DECISION:** (a) One ODM side: a room of 128 × 88 cells, a ring of 190,872, about 483 M of walkable cloud. D-1's spacing rule applies.
- **WHY:**
  - MAPS asks for about one ODM, and the source's road runs round the whole sky. A single lap at about 8 minutes on foot is an MM7 crossing, not a slog.
  - The real risk is empty road, and D-1 deals with that without shrinking the map. Shrinking would also break the Megadragon's 5,888.
- **WHO ACTS:** A6.
- **REVERSIBLE:** Until L2 only.

**Q2 Tower roofs**
- **DECISION:** (a) as drawn, plus D-4 and D-5:
  - seven roofs lead one way up and open after `m30.done`;
  - D7's hatches read the source's line and then "Bolted from below.";
  - the Pyramid's sky door works both ways after `m30.done`;
  - Alamar's hatch works both ways once unlocked from above.
- **WHY:** WORLD_DESIGN 3.3 and D-5.3 say roofs lead one way up. Gating on M30 keeps an Act III party off an Act VI map.
- **WHO ACTS:** A7 (DD-06, DD-07), A8 (DD-02, DD-03 stage 4, DD-05, DD-08, DD-14, DD-15, DD-17), A3 (the lines and gates).
- **REVERSIBLE:** Yes, per roof. Dropping a roof costs one exit and one hatch.

**Q3 Sky bandits**
- **DECISION:** (a) A toll hook plus two placed, peaceful Sky Bandits per toll (8 in all), with D-6 applied.
  - They are a new tier of about 55 in the thieves' family, in their own faction, and they turn hostile on a refusal.
  - They are not counted on the counted route. Their 7.15k goes in A2's "most experience" line (D-53).
- **WHY:**
  - The source's roads are pay-or-fight, and figures standing at the toll make the road feel inhabited.
  - Act VI absorbs the optional 7.15k: about +2 % of the act, under D-53's 1.15.
- **WHO ACTS:** A2 (row, faction, ledger line), A3 (four tolls), S (skin on the thief body, no Meshy), A6 (placement).
- **REVERSIBLE:** Yes. Falling back to (b) means removing 8 placements.

**Q4 The monster mix**
- **DECISION:** (a) 48.8k per member (+0.6 %):
  - Griffins 48 × 12;
  - Sky Golems 75 × 8;
  - Cloud Dragons 70 × 8;
  - Cloud Golems 50 × 22.
- **WHY:**
  - The griffins are the source's B1 birds, two levels under the band, as D-50 used them.
  - (c) would add a fifth family and go 7 % over for nothing.
- **WHO ACTS:** A2 (recount), A6.
- **REVERSIBLE:** Yes, cheap until placement.

**Q5 Scarab sellers**
- **DECISION:** (a) Four A3 hooks with `Xeen.payGems`, but **no new items** (the constraint forbids new equipment and icons).
  - Each purchase gives every member present a permanent **+10** to one resistance, once per character (player bits). The line: "The scarab crumbles to dust as its power passes into you."
  - Rahib's Fire scarab gives Fire, Wardoz's electricity scarab Air, Clara's cold scarab Water, and Dorion's Kinetic scarab Earth.
  - Prices follow the source's ratio, 1 : 1 : 1 : 2. A3 scales them in gem items with A2's gem ledger, so that a party that has kept its gems can afford all four in Act VI.
  - The sellers' lines stay the source's, with the numbers changed to the new prices.
- **WHY:**
  - It keeps the source's gem shop and ties it to the four planes, whose hazards deal those four elements.
  - A one-time permanent buff needs no item, no icon and no shop.
- **WHO ACTS:** A3 (hooks, prices, lines), A2 (permanent-stat ledger: four +10 resistances).
- **REVERSIBLE:** Yes.

**Q6 Olympus' ways in**
- **DECISION:** (a) Three causeways through open gilded posts, with D-8's corrections.
- **WHY:** The boats only sail up (D-5.3), so a party that comes up the rope needs a road. A town has no fortress door (WORLD_DESIGN 3.4).
- **WHO ACTS:** A6, A4.
- **REVERSIBLE:** Until L2.

**Q7 POI count**
- **DECISION:** (a) 56 by the census, with the boards hover-only (D-7).
- **WHY:** It sits within D-20's town-hub band (35–55) plus one, and D7 is a sky road with a 13-door town in it. Clickable boards would only inflate the count.
- **WHO ACTS:** A6.
- **REVERSIBLE:** Yes.

**Q8 The Megadragon**
- **DECISION:** (a) On Alamar's roof hatch at the end of its own road (6,217 from the Smoke Post), with leash 1,024. D-2, D-3 and D-5 apply.
  - The hoard holds Wyrmfang 12530 and the roof key.
  - The key is a quest item with an **existing** key picture. No new icon.
- **WHY:**
  - Q-D26 says the dragon "guards a shortcut onto Castle Alamar's roof".
  - On the Fire Corner (c) it would block M38.
  - A dead end keeps a level-125 boss optional and out of reach from every other road.
- **WHO ACTS:** A6 (roost, island move), A2 (key row, unique flag), A3 (Q-D26 qbits, hatch), A8 (DD-17 side), S (binding).
- **REVERSIBLE:** Yes. Falling back to (b) means sealing the hatch.

**Q9 The failing sun**
- **DECISION:** (a) The existing `xeen_skyroads` preset (alias `xeenroads`) for every stage, with no weather and `view_distance_scale` 2.
- **WHY:** The roads stand above the haze, so the failing sun belongs to the surface below. Adding stages later is cheap.
- **WHO ACTS:** A6 (atmosphere.yml as drawn).
- **REVERSIBLE:** Yes, one line.

**Q10 Fall landings**
- **DECISION:** (a) One `entrance:d7_fall` per surface map at the listed points, each beside a way back up.
  - Each map's owner confirms the point at install: a whole flat cell, 256 clear all round, no water or lava, and no hostile with a ranged attack within 5,888 (D-54).
  - The falls are tested in D-54's shape:
    - one fall from each of the six zones, two runs each;
    - after 20 s on the surface map, every member's HP still equals its value just after the landing;
    - a healthy level-55 party survives (D-6.2).
- **WHY:** One known landing per map, each by a way back up, keeps a fall cheap and teaches the geography. (b) would put the whole sky over one jetty.
- **WHO ACTS:** A6 (D1, D2, D4, D5, D6, `Xeen.SkyFalls` entries), A5 (D3), A3 (six zones in `Xeen.skyFall`).
- **REVERSIBLE:** Yes, per point.

---

## ANSWERS: the planes, common questions

**C1 Size and form**
- **DECISION:** (a) One compact open-air BLV per plane, 26 × 26 cells and about 44–51 M walkable. They are classed Dungeon S for textures (cap 30, at most 4 new).
- **WHY:** MAPS asks for small planes, and 30 monsters at about 45 M is a small M dungeon. Whole ODMs (c) are MM8's route, which MAPS rejects.
- **WHO ACTS:** A6.
- **REVERSIBLE:** Until L2.

**C2 Arrival from D7**
- **DECISION:** (a) No falling damage. The party lands standing on the arrival shelf, after D7's "You step off." and the engine's ordinary map change.
- **WHY:** The source does this. An arrival into an unknown arena should not cost HP or a separate survival test.
- **WHO ACTS:** A3 (`m38.corner_x` moves the party directly, without `keepHeight`).
- **REVERSIBLE:** Yes.

**C3 The test**
- **DECISION:** (a) "Accept the test of X?" raises the Sleeper's Guardian (75) and two greater elementals (70) from the pit.
  - When all three are dead, the test is passed and its qbit is set (P-1).
  - Declining does nothing.
  - If the party leaves mid-fight, the guardians stay shown on return.
- **WHY:** The source's 2,500 damage kills a party of level 56–60. A fight is the MM way to test.
- **WHO ACTS:** A3 (texts, killed-group check, qbits), A6 (hidden group, pit), A1 (confirm only).
- **REVERSIBLE:** Yes.

**C4 What the passed test opens**
- **DECISION:** (a) The gate to the sleeper's chamber, where the couch, the test's chest and the dais are.
- **WHY:** One gate gives the guardian something to guard, and there is no burning chest to explain.
- **WHO ACTS:** A6 (gate reads the qbit).
- **REVERSIBLE:** Yes.

**C5 The way out**
- **DECISION:** (a) Two ways out, both to D7's `entrance:pN_return`:
  - the way up at the arrival, always open;
  - the return dais, after the sleeper.
  - Both are `exit` presets (D-24).
  - Town Portal and Lloyd's Beacon work. Fly is not cast.
  - A6 updates `corners.yml`'s `default_way_out` to say this.
- **WHY:** The source's way out is always open, and a party that cannot pass the test must never be stuck.
- **WHO ACTS:** A6 (corners.yml, exits), A3 (two lines per plane).
- **REVERSIBLE:** Yes.

**C6 Rows and names**
- **DECISION:** (b), with one consistent naming pattern per element:
  - **Lesser X Elemental** (55)
  - **X Elemental** (62)
  - the source's name on the 70s: **Fire Blower, Whirlwind, Earth Blaster, Tidal Terror**
  - **Sleeper's Guardian of X** (75)
  - Fire's existing 11620–11623 take the pattern too (D6 shows "Lesser Fire Elemental" and "Fire Elemental"; only the names change).
  - Nine new rows: the 62, 70 and 75 tiers for Air, Earth and Water. Each is immune only to its own element (as D-47), with ids from A2.
  - Bodies: MM6's air elemental and MM7's water and earth elementals with tier skins (D-47). No Meshy.
- **WHY:** The source's names read well in Xeen's voice. One pattern keeps the four planes legible.
- **WHO ACTS:** A2 (rows, names, D6 note), S (skins).
- **REVERSIBLE:** Yes, names and rows.

**C7 Sleepers and statues**
- **DECISION:** (a) One sleeper and one couch, with four element skins, and four element statues on one common plinth with a plaque.
  - **The sleeper.** S first tries a shipped giant or titan body in a lying pose on a built Ancient-steel couch (D-49's teal steel), the glow panel from XD-19's cores. Meshy up to 30 credits only if no shipped body reads as a sleeping giant. One figure serves all four planes.
  - **The statues.** The installed elemental models, frozen in a pose and recoloured as the element's stone. No Meshy.
  - **The pedestal and the dais.** P5's disc in each element's stone.
- **WHY:** The source uses one sprite for all four sleepers and one for all four statues. Reusing the elementals as statues costs nothing new.
- **WHO ACTS:** S.
- **REVERSIBLE:** Yes.

**C8 POIs and chests**
- **DECISION:** (a) 10–12 POIs and 2 chests at treasure 6 per plane (the test's chest and one trapped cache), plus one find and one buff device.
- **WHY:** MAP_CRAFT §6's sparse-special band. Each chest has a reason to be there.
- **WHO ACTS:** A6, A2 (treasure 6).
- **REVERSIBLE:** Yes.

---

## ANSWERS: each plane's own questions

### P1 Plane of Fire

**Q1 The lava**
- **DECISION:** (a) Walkable `lavtyl` that burns as MM lava does:
  - crust banks within 64 of every lava edge;
  - ramps up every shelf;
  - P-2 holds.
- **WHY:** D-40 and D6 established that lava burns and is never water. The engine already does this.
- **WHO ACTS:** A6.
- **REVERSIBLE:** Yes.

**Q2 Vents**
- **DECISION:** (a) Nine small pressure-plate faces with the source's rule: one time in three, 50 fire damage to each member, resistance applies, line "A vent flares!".
  - None on the critical path.
  - Marked by `xpfvent`.
- **WHY:** It is the source's hazard, and the engine already supports it.
- **WHO ACTS:** A3 (event), A6 (faces, texture), A1 (confirm plates fire in an open-air sector).
- **REVERSIBLE:** Yes.

**Q3 Sky**
- **DECISION:** (a) The shipped `plane_fire`.
- **WHY:** WORLD_DESIGN §4 names it, and it costs nothing.
- **WHO ACTS:** A6.
- **REVERSIBLE:** Yes.

### P2 Plane of Air

**Q1 Falls off the islands**
- **DECISION:** (a) Below −1,500, the wind throws the party back onto the Gale Landing.
  - The fall goes to `entrance:d7_fall` in the same map, from `Xeen.SkyFallHeight` above it, with falling damage (D-6.2).
  - Tests in D-54's shape: from three islands, two runs each, HP checked after 20 s.
- **WHY:** The plane hangs over no world, and the test should not be lost to a misstep.
- **WHO ACTS:** A3 (`Xeen.skyFall` to the same map), A1 (confirm that `evt.MoveToMap` to the current map with `keepHeight` drops the party without reloading the map's state; a small general fix if not), A6 (tests).
- **REVERSIBLE:** Yes.

**Q2 Storm cells**
- **DECISION:** (a) Nine pressure-plate faces: one time in three, 50 electrical damage, line "Lightning strikes from a clear sky!".
  - None on bridges or in the Eye.
- **WHY:** It is the source's hazard.
- **WHO ACTS:** A3, A6.
- **REVERSIBLE:** Yes.

**Q3 Sky**
- **DECISION:** (a) The shipped `plane_air`.
- **WHY:** WORLD_DESIGN §4 names it, and the sky continues below the horizon (`below_horizon: sky`), so there is no world beneath.
- **WHO ACTS:** A6.
- **REVERSIBLE:** Yes.

**Q4 Monsters**
- **DECISION:** (a) Elementals only, 32.04k.
- **WHY:** The source has only elementals here. The islands and the storm give the variety. Sky Golems would be over the band.
- **WHO ACTS:** A2, A6.
- **REVERSIBLE:** Yes.

### P3 Plane of Earth

**Q1 Form**
- **DECISION:** (a) A bowl open to the `xeen_plane_earth` sky:
  - drops into the scree are real falls;
  - scree slopes lead back up to every terrace;
  - P-2 holds.
- **WHY:** One sky and one view, the weight of a cavern, and the preset already exists.
- **WHO ACTS:** A6 (check the preset under an open-air BLV).
- **REVERSIBLE:** Until L2.

**Q2 Rockfall**
- **DECISION:** (a) Nine pressure-plate faces: one time in three, 50 physical damage, line "Rocks fall from above!", plus a short `evt.CameraShake` when one hits.
- **WHY:** It is the source's hazard. Quakes on a timer would be a set piece the plane does not need.
- **WHO ACTS:** A3, A6.
- **REVERSIBLE:** Yes.

**Q3 Monsters**
- **DECISION:** (a) Elementals only, 32.04k.
- **WHY:** The source has only elementals. Onyx Golems would be over the band, and Diamond Golems under it.
- **WHO ACTS:** A2, A6.
- **REVERSIBLE:** Yes.

### P4 Plane of Water

**Q1 Water**
- **DECISION:** (a) MM9's water volumes:
  - swimming at the surface costs no breath;
  - breath lasts 15 s under water, then drowning;
  - no falling damage into water;
  - steps out of the water at every walk;
  - the outer sea's push-back from edge volumes with constant currents (approval);
  - nothing on the critical path needs swimming.
  - Water Walk does nothing on a volume yet. That is accepted and recorded, not asked of A1.
- **WHY:** The feature already runs in open-air BLVs, and a water plane you can swim in is the element.
- **WHO ACTS:** A6, A1 (confirm only).
- **REVERSIBLE:** Yes.

**Q2 Diving**
- **DECISION:** (a) No diving anywhere. The wreck's hold is half flooded and waded.
- **WHY:** A first diving puzzle in this world does not belong on a test map.
- **WHO ACTS:** A6.
- **REVERSIBLE:** Yes.

**Q3 Sky**
- **DECISION:** (a) A new preset `xeen_plane_water`, written by A6 through `make_sky.py` as data only:
  - sea-green zenith, aquamarine horizon;
  - no sun disc;
  - bright diffuse light;
  - slow cloud;
  - `below_horizon: sky`.
  - Until it lands, `plane_air`.
  - WORLD_DESIGN §4's `underwater` becomes this preset.
- **WHY:** The party swims at a surface, and `underwater` draws no sky at all.
- **WHO ACTS:** A6, orchestrator (WORLD_DESIGN).
- **REVERSIBLE:** Yes.

**Q4 Octopods**
- **DECISION:** (a) Two groups of Great Octopods (11471, 60, 5 in all), as swimmers in the volumes, with homes as in the approval.
  - S checks the swimmer binding (MM9's `floor_fix.py --swim`).
  - Fallback if the swimmers misbehave: D-52's stationary row in the two deepest basins.
- **WHY:** They are the world's only swimmers in the band, and they give a reason to keep to the walks.
- **WHO ACTS:** A2, S, A6, A1 (bug only).
- **REVERSIBLE:** Yes.

---

## ROWS AND NUMBERS

| Map | Row | Monsters | Kill XP per member | POIs / chests | Textures |
| --- | --- | --- | --- | --- | --- |
| D7 | 9114: encounter 0 (D-57), treasure 6, lock 12, trap 6, perception 6, refill 672, music 30, plains; slots kept as a record | 50 placed in 19 groups, 48–75. Uncounted: the Megadragon 125 (unique) and 8 Sky Bandits about 55 (peaceful) | **48.8k** (+0.6 %); most experience +7.15k bandits, +16.9k Megadragon | 56 (boards hover-only) / 5 at T6 | Dungeon L (cap 70), about 30; new `xsbarge`, `xsglow` |
| P1 | 9115: encounter 0, treasure 6, lock 15, trap 8, perception 8, refill 672, music 10, mountains | 30 (27 + the test's 3), 55–75 | 31.54k | 10 / 2 | S (cap 30), about 16; new `xpfvent`, `xpfglass` |
| P2 | 9116: as P1, music 9, plains | 30 | 32.04k | 10 / 2 | about 14; new `xpascorch`, `xpastone` |
| P3 | 9117: as P1, music 3, quarry | 30 | 32.04k | 10 / 2 | about 15; new `xperubble`, `xpegeode` |
| P4 | 9118: as P1, music 7, underwater | 30 (including 5 Great Octopods) | 32.38k | 10 / 2 | about 16; new `xpwspray`, `xpwcoral`, `xpwhull` (a shipped plank texture first) |

- **The planes together:** 128.0k against 124.1k (+3.1 %).
- **Act VI:** about +4.2k against MAPS, inside 10 %.
- **New textures:** at most 11, so the world goes from at most 177 to at most **188** of 450.
- **New monster rows:**
  - nine element rows (C6);
  - one Sky Bandit tier;
  - the Fire family's four renamed.
- **New quest item:** one, the Alamar roof key, with an existing picture.
- **New icons:** none.
- **Permanent ledger:** four +10 resistances (the scarabs).

**MAPS (orchestrator):**
- §0 D7 row:
  - band "48–75 (griffins 48; Megadragon 125, optional)";
  - kill XP "48.5k (L1 48.8k, +0.6 %, D-58)".
- §0 P1–P4 row:
  - kill XP "124.1k (L1 128.0k, +3.1 %, D-58)".
- §3 D7 row:
  - content adds "three causeways to Olympus; four tolls with peaceful bandits; scarab sellers paying in gems (permanent resistances); the Megadragon on Alamar's roof hatch at the end of its own road (D-58)";
  - notes "open-air BLV, 128 × 88 cells; falls to one `entrance:d7_fall` per surface map".
- §3 P row:
  - notes "26 × 26-cell open-air BLVs: Fire a lava crater, Air islands, Earth a bowl, Water a drowned temple; the test raises the guardians; the way up always open (D-58)".

---

## RELAYS

- **A1:** Confirm only; no new engine work is expected.
  1. Hidden placed actors can be shown mid-visit in an open-air BLV (shared with D-56 relay 1).
  2. `PressurePlate` faces fire in an open-air sector.
  3. `evt.MoveToMap` to the current map with `keepHeight` (P2's falls) keeps the map's state. A small general fix if it does not.
  4. Water volumes, constant currents and swimmers behave under an open-air BLV's outdoor view, as on MM9's maps.
  - Water Walk on volumes stays open and is not required.
- **A2:**
  - **Map rows.** 9114–9118 as in ROWS, with bolster rows.
  - **Element rows.** The nine C6 rows, the Fire family renamed (check D6's notes), and 11623 renamed "Sleeper's Guardian of Fire".
  - **Sky Bandit.** A thieves' tier of about 55 in its own faction, peaceful.
  - **The Megadragon and its hoard.**
    - The Megadragon 11654 is unique.
    - Wyrmfang 12530 goes in the hoard.
    - The roof key is a quest item with an existing key picture.
  - **Ledger and recount.**
    - Four +10 resistances in the permanent ledger.
    - The Act VI recount: D7 48.8k, planes 128.0k.
    - The "most experience" line: bandits 7.15k, Megadragon 16.9k.
    - The gem ledger for A3's scarab prices.
- **A3:**
  - **Tolls and roof gates.**
    - Four tolls, with D-6 rules.
    - The roofs' "shut fast" line before `m30.done`, and the hatches' "Bolted from below." (D7) and "Bolted from above." (DD-17) lines.
  - **Merchants, lamps, bottles.**
    - Four riddles.
    - Three Q-D27 lamps.
    - Four bottles.
    - Four scarab hooks (Q5): prices, lines, player bits.
  - **Corners.** The question flow: "What do you seek?", then `m38.corner_<element>` moves the party directly; any other answer runs `corner_wrong`.
  - **Q-D26.** The kill qbit, the hoard, the key and the hatch-unlock qbit.
  - **Falls.**
    - D7's six fall zones in `Xeen.skyFall`.
    - P2's fall to the same map.
  - **The planes.**
    - Test qbits 111764–111767 and the killed-group check.
    - The way-up and dais lines.
    - Four hazard lines.
    - Device and find lines.
  - **Original lines.** ORIGINAL_LINES rows for aaze0025–0028, aaze0089–0099 and aazex100–112.
- **A4:**
  - `d7.yml`'s 13 doors and the mirror as drawn.
  - `olympus_square` (-4608, 6400, 1792) and `olympus_dock` (-640, 3200, 1792).
  - No vendor houses (Q5).
- **A5:** D3's `entrance:d7_fall` at (-15360, 11776, 1440), facing east, confirmed under Q10's rule at D3's next install, plus its fall test.
- **A6:**
  - **D7.** Apply D-1 to D-8 and L2.
  - **The surface.**
    - `entrance:d7_fall` on D1, D2, D4, D5 and D6, plus `Xeen.SkyFalls` entries and Q10's tests.
    - D1's `entrance:d7_rope`.
  - **corners.yml.** The C5 `default_way_out`.
  - **The planes.** P-1 to P-4 and the concept corrections.
  - **Sky.** `xeen_plane_water`.
  - **Textures.** Register the 11 new textures after they are made.
- **A7:** Roof stairs from DD-06 and DD-07 up to `entrance:dd06_roof` and `entrance:dd07_roof`, opening after `m30.done`.
- **A8:**
  - Roof exits up from DD-02, DD-03 (stage 4), DD-05, DD-08 and DD-14, opening after `m30.done`.
  - DD-15's sky door both ways after `m30.done`.
  - DD-17's hatch: "Bolted from above." until it is unlocked from D7, then both ways.
  - DD-26's stair both ways.
- **S:**
  - **Shared with P5:** the Rest Stop hut and blank boards.
  - **D7 set pieces:**
    - four element-tinted barges;
    - the celestial boat;
    - the genie lamp (D5/D6's).
  - **Bodies and bindings:**
    - the Megadragon binding (11654) on the MM8 dragon, scaled, no Meshy;
    - the Sky Bandit skin on the thief body;
    - element tier skins for the nine rows;
    - the octopods' swimmer binding.
  - **The planes' pieces:**
    - the sleeper and couch with four skins (C7; Meshy up to 30 credits only if no shipped body reads);
    - four statues from the elemental models;
    - the pedestal and the dais;
    - the way-up effects;
    - the per-plane devices (font, singing stones, geode, tide pool, bell, wreck).
- **AU:**
  - X8's wind bed on D7;
  - a hum in each corner's element;
  - Megadragon and cloud-dragon calls;
  - the bandits' whistle;
  - per plane, a bed of lava, gale, rumble or surf.
  - All CC0 or our own.
- **Orchestrator:**
  - Add D7 and P1–P4 to `world.yml` `openAirMaps` at install.
  - Update the MAPS rows above.
  - WORLD_DESIGN §4: the water plane's sky is `xeen_plane_water`.
  - MONSTERS_AND_ITEMS: the element rows' names and the Sky Bandit.
  - Add the DECISIONS row.
  - Close A6's DECIDE items.

---

## SUMMARY ROW

| D-58 | 2026-11-21 | D7 The Skyroads and planes P1–P4 L1 | All five approved with changes. D7: ring 191k, road gaps ≤ 8,192; seven roofs one way up after M30, Pyramid both ways, Alamar both ways once unlocked from above; tolls with 2 peaceful bandits (uncounted, paid tolls stay open); 48.8k; scarabs as permanent +10 resistances for gems (no items); Megadragon unique, castaway isle ≥ 5,888 off; `xeen_skyroads`; six landings tested (D-54). Planes: 26×26 open-air BLVs; test raises 75 + 2×70, passed in qbits 111764–111767; way up always open; source names on the 70s; 128.0k; `xeen_plane_water`. Detail: `briefs/d7/L1/D58_DECISION.md` | A1, A2, A3, A4, A5, A6, A7, A8, S, AU, orchestrator |
