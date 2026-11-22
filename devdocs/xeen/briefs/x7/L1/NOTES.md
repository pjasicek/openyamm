# X7 Mount Firestone: L1 plan (MU-3, MU-4) for the phase 5 review

A5, 2026-11-20. This is a plan only: there is no geometry. Nothing is built until a decider has approved the board
(`output/studio_cal/x7/mockups/board_x7.png`). `output/studio_cal/x7/tools/gen_l1.py` writes the four YAML files
here (project, plan, sketch, atmosphere). To change them, edit the script, then run `output/studio_cal/x7/tools/run.sh`.
It generates the files, runs `oymap fmt`, renders, writes the census into `totals`, runs `oymap validate --assets
assets_dev` and draws the board. The Python steps run under an 8 GB cgroup cap. Validation: no issues.

## What the plan holds

**Sources:** Clouds E1 (north-west), F1 (north-east), E2 (south-west) and F2 (south-east), plus D1's lava lake and
Dragon Tower (MAPS X7). They are pressed into the land inside the rims.

**Rims:** the north rim is at y 24 (as X4's north rim) and the east rim at x 104 (as X1's east rim). The playable
land is x 19-104, y 24-109.

This is a trap map. The Red Dwarf Range crosses the whole map: the south is mild, the range is quiet and the north is
deadly.

- **The south slopes (E2, F2): orcs only.**
  - Red stony ground rises from X1's hills. The north road (x 69) climbs past the slope fork to the range.
  - **The dwarves' watch** stands beside the road: a stockade with a signal tower. It is abandoned, but its pay chest
    is still there.
  - **Sablewing (4720, D-5.2)** sits at a cave mouth under a red crag, off the road from X1 at [76, 90]. He is 4,400
    from any fight.
  - The Shrine of Fire stands on a knoll west of the road. The Well of Speed is by the old west track.
  - An **orc outpost to burn** (source E2) stands on the west slopes. It has three placed orcs and a chest.
  - **XD-05's back gate** is at [88, 100], barred from inside (110051). Next to it is the orcs' den, with a chest.
  - The hot spring stands in the south-east.
  - Orcs fill two areas: the west slopes, and the Red River Basin round the back gate.
- **The Red Dwarf Range: quiet.**
  - Peaks reach 3,200. The Firestone road from X4 (y 66) climbs its valley to **the Firestone Gap** (2,300), where it
    meets the north road.
  - On the Gap's north lip stands the **obelisk** (obelisks.x7, SPHINX). It is on safe ground: from there the whole
    north lies below.
  - Also in the range: the cairn of the unreturned, a miner's cache, and the dwarves' east lookout (a landmark).
- **The north: hydras, dragons and lava golems.**
  - **Ash flats (E1):** north of the Gap, the lava fork leads to three places:
    - the black bridge over the lava river;
    - the **Volcano Cave (XD-16)** at Firestone's west foot, between a demon idol and a devil idol;
    - **Shangri-La's cleft (XD-17)** just east of the cave, which opens on q-c26.done.

    The north track goes on over the bridge, past a knight's remains (a chest), to the **Dragon Cave (XD-18)**. Its
    cave is in a black crag at the rim, with the Dragon Tax Office inside its mouth (D-5.2). Hydras live here.
  - **The lava basin (D1):**
    - The lava lake (1,500) holds a cooled-flow island, joined to the shore by a causeway. On the island lies the
      **Ever-Hot Lava Rock** (q-c14.lava_rock), guarded by eight placed Lava Golems (55).
    - Also here: the hydras' wallow (a chest), and the **Dragon Tower (FD-04)** on its crag over the lake's north
      shore at the rim.
    - Hydras live here.
  - **Mount Firestone (F1):**
    - A black cone rises to 5,000 under a smoke plume. Its crater holds a lava pool (4,600).
    - The lava river runs down the west flank to the lake. Its north arm pours over the south wall of **the lava
      cove** into the stars. The cove bites four cells into the north rim at x 68-78.
    - On the east shoulder lies a dragon's hoard (a chest). The **Fire Reflector** (m37.reflector_fire) stands on the
      corner spit.
    - Dragons live here. They are at least 6,100 from the Volcano Cave and 8,600 from the tax road.

## Figures (render_x7.py, `output/studio_cal/x7/mockups/figures.json`)

| Figure | Target | Plan |
| --- | --- | --- |
| Obelisk; device kinds | 1; >= 4, one permanent | 1 (the Gap's north lip). Devices: a well, a shrine, the hot spring, the cairn, the idols, the hot rock, the Reflector, the outpost to burn. Permanent: the Well of Speed (+2 Speed; question 2) |
| POIs | MAPS trap band 22-28 | **24** by the D-20/D-15 census (chained within 400; dungeon doors in; Sablewing, landmarks and junctions out). The idols and XD-16's door, and the outpost and its chest, are one cell apart here. At L3 each pair stands within 400 (one set piece, one spot), which gives 22 |
| POI spacing | 1,300-2,600 | nearest-neighbour median 3,280 (510-10,440). The north is sparse by design |
| Dungeon entrances | 3-6 | 5: XD-16, XD-17 (the cleft), XD-18, FD-04, XD-05's back gate. Each is sealed until its map exists |
| Outdoor chests | 4-10, a reason each | 7: the watch's pay chest, the orc outpost, the orcs' den, the miner's cache, the knight's remains, the dragon's hoard, the hydras' wallow |
| Spawn markers; hostiles at load | 45-70; 90 (trap band 90-110, +-15 %) | 47 markers; **101** hostiles: 90 from markers and 11 placed (8 Lava Golems 11593, 2 Orcs 11030, 1 Orc Guard 11032) |
| Kill XP per member | 76.4k +-15 % | **75.9k** (-1 %): dragons 37.0k (Dif 5, mean level 69), hydras 31.2k (Dif 3, mean 52), golems 7.2k, orcs 0.6k |
| Encounter areas (4,096²) | 3-8 of 6-30 | 5: lava basin 9.7, ash flats 7.7, Firestone 12.9, west slopes 7.5, Red River 6.0 |
| Quiet land | >= 1/3 | 59 % (the range and most of the south) |
| First fight, map-edge arrivals | 2,000-6,000 | X1 road 4,400; X4 road 4,900 (orcs in both cases) |
| The trap's safe edge | — | North monsters are 5,200 from the north road and 5,400 from the Gap. The nearest dragon is 26,100 from the X1 arrival |
| Roads | 1-4 % | 1.3 % road (+ 4.0 % lanes) |
| Relief inside the box | >= 2,500 | **1,380-4,730 = 3,360** on the drawn land (from the X4 road's valley to Firestone's rim). The sketch's points run 1,400-4,900 |
| 6,000 rule; wild land (D-11.5) | none over 6,000; <= 0.16 | farthest land 5,700 (at [57, 108]); 0.085 of the land over 3,000 from a place. The places include seven event-less landmarks: the east lookout, slag heaps, boundary stone, dragon skull, fallen cart, pony shed and charcoal pits |
| Towns | — | none (wilderness; x7.yml has no houses) |
| Textures | outdoor cap 120 | Kits: cloudside_town fieldstone and timber (the watch), towers (the Dragon Tower in black stone), ancient (the Reflector). Ground: MU-2's X7 set (gravel_volcanic, ground_crust, rock_cliff tinted, soil_stony; slag_crust is MU-2's open gap). No new textures named. Estimate 40-60 distinct face textures (no town). Lava needs a liquid set (requests) |

The census spots (24) are:
- five entrances;
- the obelisk;
- the Shrine of Fire;
- the Well of Speed;
- the Fire Reflector;
- the lava rock;
- the idols;
- the hot spring;
- the cairn;
- the orc outpost;
- seven chests;
- three signposts (the Gap, the lava fork, the slope fork).

Monsters (A2's rows exist; the slots still need A2's map_rows entry, see requests):
- Slot 1, Xeen Orc, Dif 1, [2, 3]: Orc 5, Orc Archer 7, Orc Guard 10. 10 markers.
- Slot 2, Xeen Hydra, Dif 3, [1, 3]: Hydra 45, Venomous Hydra 55, Great Hydra 65. 19 markers.
- Slot 3, Xeen Dragon (cloud_dragons), Dif 5, [1, 2]: Water Dragon 60, Acid Dragon 66, Fire Dragon 75. That is 10/50/40
  %: mostly MAPS' "acid and fire". 18 markers.
- Placed: Lava Golem (11593, 55) ×8 on the island.

MAPS' "C 85" is the Frost Dragon tier (11643). It is not in any slot mix and stays in XD-18.

Under D-1.2, the trap dragons (75) count in Act V (60 % of 75 is 45, and Act V leaves at 58).

The map_stats are in project.yml: 9105, continent 6, treasure 5, lock 10, trap 5, perception 5, music 26,
environment mountains.

## Choices

- **Edges:**
  - South, x 69: X1's north road reaches its y 0 at x 69. Its built edge row is 1,600, with the road at 1,856. X7
    draws a level span 64-74 at 1,850 and ridges either side that meet X1's hills.
    - X1 seals its north edge today, and A5 reopens it when X7 is installed: the level span and edge:north to
      xeen_x7.odm.
  - West, y 66: X4's Firestone road (its east spans) carries straight on:
    - rim 0-24;
    - lava fields 24-60 at 1,800-2,600;
    - the road 60-72, level at 1,300;
    - red dwarf hills 72-128 at 1,900-2,700.

    X4 seals its east edge until X7 exists.
  - X4's arrival from X7 is entrance:east_road [107, 66.5]. X1's arrival from X7 is entrance:north_road [69, 21].
- **Rims:** north at y 24, east at x 104. The north-east corner is Cloudside's Fire corner (M37).
  - The lava cove (x 68-78, four cells deep) is drawn so that the falls pour toward the signature camera. This is
    D-35's lesson from X6's sand-falls, which showed only their backs.
- **Doors** (no dungeon brief places them yet; these are proposals for A7 and A5):
  - XD-16 at [66, 45], facing west, between the idols.
  - XD-17's cleft at [73, 48].
  - XD-18 at [56, 30], facing south in the rim crag.
  - FD-04 at [29, 32], facing south on the crag over the lava lake.
  - XD-05's back gate at [88, 100], facing west.
- **Moved from the source:**
  - The lava rock moves from E2 (7,11) to the lake island (MAPS; question 4).
  - The Volcano and Dragon Caves (both in E1) sit at Firestone's west foot and on the rim.
  - D1's lava lake and Dragon Tower come in from the west.
  - The Shrine of Fire and the Well of Speed stay in E2 (the south-west).
- **Added devices and landmarks** (needed for the 6,000 rule and D-11.5's figure): the cairn, the hot spring and the
  seven event-less landmarks listed in the figures table.
- **The dwarves' watch** is MAPS' "dwarf outpost on the south slope". It is drawn abandoned, because x7.yml has no
  people (question 8).

## MU-4 concepts

`tools/paint_x7.py` made two `codex exec` calls, one per view, with no retries. Both came back on the first attempt.
The results are `output/studio_cal/x7/mockups/raw/x7_arrival_v1.png` and `x7_signature_v1.png`, with their prompts
(.txt) and logs (.log) beside them.

- **Arrival**, from X1's north road at [69, 106], looking north-north-east. The painting shows:
  - the pebbled road up red stony slopes with dry grass and thorn scrub;
  - the abandoned dwarf watch on the left, with its stone signal tower and brazier;
  - Sablewing's cave on the right, with a cooking fire and the hoard glinting inside;
  - the range across the view;
  - Mount Firestone's cone smoking beyond, with a red glow at its crater;
  - the Dragon Tower tiny on the far left;
  - ash flakes in a dull sky.

  It follows the blockout. Against the plan:
  - The range reads as low rolling hills, not bare peaks, and the Gap's saddle is not shown.
  - The road is wider than 3-4 m and cobbled.
  - Both get fixed at L3, where the plan wins.
- **Signature**, from the lava cove's west lip at [67, 25], looking south-east. The painting shows:
  - the lava river pouring over a sheer black basalt cliff into a starfield, with sparks trailing into the void;
  - Firestone smoking above, its lava river down the flank;
  - a small pale machine (the Reflector) on the far-left spit.

  Against the plan:
  - The cliff is painted as a straight rim seen side-on, not a cove.
  - **A stone hut with an awning, and a castle on a mesa, appear on the right.** Both leaked from the X6 reference
    picture (Saul's hut and Castle Basenji). They are not in the plan and are to be ignored at L3: X7's north has no
    buildings except the Dragon Tower in the west, which is out of this view.
  - The lava falls need a decoration model, a translucent, scrolling, emissive one like X6's sand-falls (requests).

## Original lines (to wire at L4; A3's hooks and the map's own events)

- "Enter the Volcano Cave?" (`xeen/aaze0017:1`): XD-16's door.
- "The Dragon Cave smells pretty bad. Are you sure you wish to enter?" (`xeen/aaze0017:0`): XD-18's door.
- "You have found an Orc Outpost. Put it to the torch?" / "The Outpost burns well." (`xeen/aaze0018:3-4`): the orc
  outpost (the source's +1,000 experience goes to A3's scale).
- "Shrine of Fire" / "You don't think anyone is listening." (`xeen/aaze0018:5-6`): the shrine.
- "The water is cool and refreshing." (`xeen/aaze0018:0`): the Well of Speed.
- "You have found a rock that is still hot from an ancient volcanic eruption! Strangely, you are able to pick it up
  without getting burnt." (`xeen/aaze0018:8`): suggested for A3's q-c14.lava_rock text.
- "Reflector. Activate?" / "The machine hums quietly." (`xeen/aaze0021:0-1`): the Fire Reflector.
- "Crude furnishings and filthy bedding tell you that orcs have been living in this cave. Pillage?"
  (`xeen/aaze0022:1`): the orcs' den beside XD-05's back gate.

## Quest hooks placed

- **On the map:**
  - obelisks.x7 (the obelisk);
  - q-c14.lava_rock (the island);
  - m37.reflector_fire (the Fire corner).
- **Doors:**
  - XD-05's gate reads x1-tam.orc_back_gate_open (110051);
  - XD-17's cleft reads q-c26.done (112522).
- **New map events:**
  - the orc outpost (a burn hook: A3 or map-local);
  - the idols (Q-C26's hint, flavour);
  - the cairn (+Luck, daily);
  - the hot spring (heals, daily);
  - the Shrine of Fire (+Fire resistance, daily);
  - the Well of Speed (+2 Speed, permanent).
- **People outdoors:** Sablewing 4720 (Dragon Master, A4's teacher).

## Requests (for the orchestrator to relay; none of these files is A5's)

- **A2:**
  - X7's map_rows entry:
    - slots: orcs tier 1 [2, 3] weight 21; hydras tier 3 [1, 3] weight 40; cloud_dragons tier 5 [1, 2] weight 39;
    - perception 5, environment MOUNTAINS;
    - placed rows 11593 ×8, 11030 ×2, 11032 ×1.

    Today `X7: {lock: 10, trap: 5}` has no slots, and map_stats.txt has no 9105 row.
  - `row_before_install: true` once L4 starts.
  - The Act V recount at 75.9k.
- **A1:**
  - A word for ash fall. Either atmosphere.yml gets an `ash` chance written to engine `rendering/weather/weather.yml`'s
    per-map `ash`, or there is a world-level weather row for `xeen_x7.odm`. Today only that engine file can give ash,
    and atmosphere.yml's `precipitation` knows only rain and snow.
  - A **lava liquid** for the Xeen world. Its MM7 tile table has no lava set, and `oymap validate` refuses `tile_set:
    lavtyl` on the lava lake, crater and rivers. Lava is drawn as plain water bodies until there is one.
  - X7's edge_spans and outdoor_travels rows once X7 is installed (generated).
- **A3:**
  - q-c14.lava_rock's `where`: "on the cooled-flow island in the lava lake under the north rim" (question 4). The
    original line aaze0018:8 is suggested for its text.
  - The orc outpost's burn hook (x7.orc_outpost, aaze0018:3-4).
  - Confirm that XD-17's X7 cleft reads q-c26.done (question 3).
- **A4:** confirm Sablewing's place as [76, 90] (the cave mouth off the X1 road). Add one houseless dwarf lookout only
  if question 8 says so.
- **A7:**
  - The door proposals above: XD-16 [66, 45] facing west, XD-18 [56, 30] facing south (the tax office just inside),
    FD-04 [29, 32] facing south.
  - Door heights and footprints for L3.
  - XD-05's back gate: open its rockfall and point its exit at X7's [88, 100] once X7 is installed.
- **S / A6:**
  - A lava-fall decoration model (emissive, scrolling, like X6's sand-fall).
  - Demon and devil idol models, unless the engine MM6 statues serve.
  - Black-basalt rock for the Dragon Tower's crag.
- **A5 (own):** reopen X1's north edge when X7 is installed. XD-17's exit arrives at the cleft.

## Open questions for the decider

1. **The south slopes' band.** MAPS says south orcs 5-12, the trap map's safe edge, which an X1 party reaches at
   level 4-7. x7.yml and D-5.2 say "levels 20-30" for Sablewing's slope.
   - Options:
     - (a) Orcs 5-10 at Dif 1, as drawn. Read 20-30 as the party band for the Master teacher.
     - (b) The orc warband (16-26) round the west outpost.
     - (c) Both: orcs by the roads and the warband in the west.
   - Recommendation: (a). It is cheap to reverse: a slot change.
2. **The Shrine of Fire twice.** X4 (built) already has a permanent Shrine of Fire.
   - Options:
     - (a) X7's shrine temporary (daily), with the Well of Speed (+2 Speed, the world's only permanent Speed) as the
       map's permanent device. This is what is drawn.
     - (b) X7's shrine permanent, as the source's E2 shrine, and X4's made temporary. This needs an X4 rebuild and
       re-bake.
     - (c) Both permanent.
   - Recommendation: (a).
3. **Shangri-La's way back in.** The valley has no mirror and no Town Portal (D-5.1).
   - Options:
     - (a) A cleft east of the Volcano Cave that opens on q-c26.done, as drawn.
     - (b) Only through XD-16 on every visit, as in the source.
     - (c) The cleft opened from inside on the first visit.
   - Recommendation: (a). It also gives XD-17 its exit.
4. **The Ever-Hot Lava Rock.**
   - Options:
     - (a) The island in D1's lava lake (MAPS), guarded by 8 placed Lava Golems (55) and reached from the Gap
       through hydra country. This is what is drawn.
     - (b) The crater's rim, per q-c14's hook text, which puts it in dragon country.
     - (c) A lava pool on the range's south side. That is safe for Q-C14's level 35, but contradicts MAPS and the
       hook.
   - Recommendation: (a). The Widget is first needed in M40 (Act VI). A3 rewrites the hook's place.
5. **The north's mix:** hydras Dif 3 [1, 3], dragons Dif 5 [1, 2] and 8 placed golems. That gives 101 hostiles and
   75.9k.
   - Options:
     - (a) As drawn.
     - (b) Dragons at Dif 4 (more Water Dragons; MAPS names acid and fire).
     - (c) Trim to about 90 hostiles by dropping two hydra markers (about 71k).
   - Recommendation: (a). Both figures are inside their bands.
6. **The tax road.** The north track to the Dragon Cave crosses hydra country; dragons stay 8,600 from it.
   - Options:
     - (a) As drawn: D-5.2's "before the first dragon" is read as inside XD-18.
     - (b) A keep-clear corridor along the track, moving the ash-flats markers to the lava basin.
   - Recommendation: (a). The Great Wyrm promotion is at about level 50, inside the hydras' band.
7. **The signature view.**
   - Options:
     - (a) The lava cove at the north rim, as drawn. It is earned, and the falls face the camera.
     - (b) The whole north from the Gap. That view is safe, but the falls are far and seen side-on.
   - Recommendation: (a), with the Gap as a tour shot.
8. **The dwarves' watch.**
   - Options:
     - (a) Abandoned: x7.yml has no people, and the pay chest is left behind. This is what is drawn.
     - (b) A4 adds one houseless dwarf lookout with a warning line.
   - Recommendation: (a). It needs no stand-in.
9. **The sky.**
   - Options:
     - (a) Cloudside's fair preset with A6's ashen theme (`xeen_x7.odm: ashen` is already in the world sky.yml),
       plus ash fall on about 40 % of days (WORLD_DESIGN 4).
     - (b) MAPS' `ember` / `plane_fire` look.
   - Recommendation: (a). The lanes' rule is that Cloudside maps use the shipped presets.

## Files

- Brief: `devdocs/xeen/briefs/x7/L1/{project,plan,sketch,atmosphere}.yml` (this folder).
- Scripts in `output/studio_cal/x7/tools/`:
  - `gen_l1.py`, the brief;
  - `render_x7.py`, the drawings, figures and census;
  - `paint_x7.py`, the Codex concepts;
  - `board_x7.py`, the board;
  - `run.sh`, the whole chain.
- Drawings in `output/studio_cal/x7/mockups/`:
  - `plan_x7.svg`, `plan_x7.png`, `plan_x7_2x.png`;
  - `blockout_arrival.png`, `blockout_signature.png`;
  - `board_x7.png`, `figures.json`;
  - the raw Codex returns in `raw/`.
