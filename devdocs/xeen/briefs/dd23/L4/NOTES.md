# DD-23 Gargoyle Lair: L4 notes

Lane A7 phase 4, ninth session (agent `xeen-a7-dd23`), 2026-11-20. Map 9176, `xeen_dd23.blv`, class S, `world: xeen`
from L1, in Magic Mountain's eastern crags on D4 (Lakeside and Blackfang). Built from the MU-6 graph
`devdocs/xeen/mockups/act4_graphs/dd23.graph.yml` with D-39 (`mockups/act4_a7_decisions.md`, DD-23 rows 1-5, which
win): 15 placed gargoyles, one Gargoyle Overlord 45 on the highest rock, MM7 7d07 rock, MM6 straw on the nest, snow a
floor texture under the crack, `open_sky` with the Darkside preset by its own name, no doors, the rocks stay broken
and no stage. Q-D15 Caleb's Magnifying Glass.

**State: done in the scratch root `output/studio_cal/dd23/root`, not in assets_dev.** The root is phase 3's recipe
(hard links, real copies of `worlds/xeen/maps`, `events/maps` and every data table by `copy_tables.py`) with test rows
9176 in its `map_stats.txt` and `bolster_maps.txt` (from 9149's, slot `Xeen Mountain Gargoyle` tier 1, treasure 4,
music 31, CAVE, continent 7). A2 writes the real rows; the lane lead installs and bakes.

Scratch: `output/studio_cal/dd23/` — `tools/gen.py` writes every project file (**edit gen.py, never the YAML**;
`gen.py --levels` writes L1-L3); `cycle.sh` regenerate, fmt, validate, build, install into the scratch root, audit
`--reach --solve`; playtests through the lane's `output/studio_cal/a7/xfour.sh` (`ROOT=<abs root> KEY=dd23`);
`shots.sh` + `shots.yml` the tour; `tools/sheet.py` texture contact sheets (`tex/`).

## What was built

x east, y north. The mouth opens south at y 0 (D4 lies south of it); floor 0 runs north, floor 640 above.

| Room | Floor | Size | Monsters (placed, group) | What |
| --- | --: | --- | --- | --- |
| Cave mouth | 0 | 768 square, corners broken | — | **Start and entrance:d4_mouth** (0, 256) facing north; the exit to D4 in its south wall (`xdcraglt`, D-45) |
| Guano slope | 0 | 640 × 1,280, 448 high | 3 Mountain Gargoyle (10) | Droppings, bones, two stalactites; the bone ledge's cleft off its west wall |
| Bone ledge | 0 | 640 × 512 | 1 Mountain Gargoyle (11) | The climber's corpse and his pack (chest T4) |
| Perch hall | 0 | 1,408 × 1,152, 1,216 high | 2 Mountain Gargoyle on the perches, 1 Gargoyle Sentinel (12) | Two perches on its walls (352 and 320 high), three stalactites; the upper perches' lip over its north side |
| Rock ramp | 0 → 640 | 256 wide, about 1,700 long | — | Behind the hall's west wall: level 192, climbs 640 over 1,344 north, level 192 into the upper perches |
| Still gallery | 0 | 1,024 × 896 | 3 Mountain Gargoyle (13) | Three weathered rock pillars like statues; the rock steps from its north end |
| Rock steps | 0 → 640 | 320 × 1,024 | — | 16 steps of 40 north to the roost |
| Upper perches | 640 | an L, 384 wide | 1 Mountain Gargoyle (14) | The ledge over the perch hall (open along its lip: a drop of 640) and the ledge walk north to the roost |
| The roost | 640 | 1,536 × 1,408, 1,152 high | Gargoyle Overlord (on the highest rock), 1 Sentinel, 2 Mountain Gargoyle (15) | The crack of sky, the snow drift under it, five roosting rocks in a ring |
| Nest of shiny things | 640 | 640 × 512 | — | Straw floor, the nest (Caleb's glass), the hoard (chest T4) |

**Counts and sizes.** 10 rooms = **10 sectors** (11 with the BLV's sector 0; S ≤ 15), 621 faces, floor **9.82 M
units²** (`oymap metrics`; S ≤ 20), footprint x -1,216 .. 2,176, y 0 .. 6,528, two levels 640 apart. **15 monsters**,
all placed (S 15-30): Mountain Gargoyle 11550 (30) × 12, Gargoyle Sentinel 11551 (38) × 2, Gargoyle Overlord 11552
(45) × 1 on the highest rock (D-39 (2), no boss row). Kill XP per member L(L+10) × n / 4: 12 × 1,200 + 2 × 1,824 +
2,475 = 20,523 / 4 = **5.13k** (D-39 (1)). **2 chests**, T4 (the climber's pack 600 gold + 1 roll; the nest's hoard
1,000 gold + 2 rolls, trapped 3). **0 doors** (see the exception below). 1 loop (ramp and ledge walk up, rock steps
and gallery down) plus the drop off the upper perches' lip.

**Textures (13 distinct, 1 new; S cap 30).** MM7 Thunderfist 7d07's cave rock `c2b` (256, walls, roofs, pillars,
stalactites, the roosting rocks) and its rock floor `cfb1` (128 at scale 2); MM6 `straw` (the nest's floor and the
nest's top); MM7 `7snow` (the drift under the crack, a floor: no weather indoors); XD-05's poles `t66abc10a` (the
nest's rim of sticks); the new Darkside crag view `xdcraglt` (D-45 (2); the mouth's exit, fitted once; it replaced DD-13's `xddaylt`, the
fallback); the world's plain chest
(`ch1frle`, `ch1frntb`, `ch1frre`, `ch1side`, `ch1tople`, `ch1topb`, `ch1topre`). Every texture has one size in the map.
The crack's top is `c2b` with `sky: true` (drawn as the sky).

**Open sky.** `atmosphere.yml`: `open_sky: {mode: open, preset: xeen_darkside_day}` (the preset by its own name, never
the alias `xeendark1`); the roost's `ceiling_levels` chimney (the crack's outline, 512 high over the roost's 1,792
ceiling; 2,944 at first showed only a sliver of sky) has its top as the sky. A daylight-coloured light (140, 134, 124)
hangs under the crack, the wind sound (`whistling wind`) at the crack and at the mouth.

**Map card (A2's row 9176, landed 2026-11-20).** Music 31; environment cave; treasure 4; lock 6, trap 3, perception 6;
refill 672; bolster LowerToEqual; **encounter 10** (D-39's rest rule: from the map's own hostile row); slot 1 `Xeen
Mountain Gargoyle`, tier 1, [2, 3], weight 100.

## The roost (Q-D15, D-39 (5))

- **The question** on every roosting rock (`evt:rock_*`, platforms `platform:rock_*`) and on each rock's worn foot
  (`evt:heap_*`, `platform:heap_*`, 16 high, 288 across): the source's line "Do you wish to destroy the Gargoyle
  Lair?" (dark/aaze0021:6) in the question window, "Destroy (Yes/No)?". No: "You leave the roosting rocks standing."
  (asked again next click). Yes: A3's hook `q-d15.roost` (aaze0021:7 "With great effort, you pound roosting rocks to
  powder and scatter the dust to the wind.", lair_destroyed 113301) and all five rocks destroyed
  (`destructible:rock_*`, stone, `trigger_only`: blows do not break them, so the quest cannot be skipped; sound
  `xeen/xeen_sphinx_stir.wav`, the world's stone grinding, since MM9's default stonecrumble is not in Xeen's audio).
  The destructibles' state is saved with the map: they stay broken (reload checked in `playtest.yml`).
- **After:** the five feet stay as dust heaps; a click runs the hook again, which shows A3's else text "Rock dust. The
  gargoyles will have to sit somewhere else." The remaining gargoyles stay (no stage).
- **The nest** (`evt:nest`, `platform:nest`): A3's `q-d15.glass` gives its text and Caleb's Magnifying Glass 12352
  once (glass_found 113302), then "Spoons, buckles, broken mirrors."

## Exit and arrival (D-24, D-37)

- **Way out (live):** `exit:mouth` in the mouth's south wall (`exit` preset, the game's leave window) → neighbour
  `exit:d4_mouth`, `to: xeen_d4.odm`, `arrival: entrance:dd23_lair` (A6's named arrival (-9216, 10752, 2304) facing
  south, 1536; the build's MoveToMap carries it). **Measured:** the party stands at **(-9216, 10752) z 2,305** on
  landing and 2 s later (`playtest_exit.yml`, z 2,290-2,330).
- **Named arrival for A6:** `entrance:d4_mouth` in `room:mouth` at **(0, 256, 0) facing north (512)**, 256 inside the
  mouth, daylight behind (objects.yml `arrivals`; the installed `xeen_dd23.studio.yml` lists it with `start`). D4's
  `thing:dd23_lair` still says the lair comes later: A6 points it at `into: {map: xeen_dd23.blv, arrival:
  entrance:d4_mouth}` after the install.

## Original lines

- "Do you wish to destroy the Gargoyle Lair?" (dark/aaze0021:6): the roosting rocks' question.
- "With great effort, you pound roosting rocks to powder and scatter the dust to the wind." (aaze0021:7): A3's
  `q-d15.roost` (experience dropped).
- "Gargoyles like shiny things." (dark/aaze0019, Caleb; A3's paraphrase in q-d15): the nest's line on entering ("Straw,
  and in it everything that glitters: spoons, buckles, broken mirrors. Gargoyles like shiny things.").

## Checks (scratch root, binaries of merge point 17)

- `oymap fmt --check` clean (L1-L4); `validate` L1-L4 no issues (against the root and assets_dev); `build` **0
  warnings**; `audit --reach --solve` (`output/studio_cal/dd23/audit.txt`): **no error, no warning**: `lights.*` 0,
  doors 0, `textures.*` 0, dressing 0, faces in one plane 0 pairs; on foot from the start 10 of 10 sectors; `solve`
  never reached 0. One info: `texture.squashed` on the exit's `xddaylt` (fitted once over its 384 × 320 face, as
  DD-13's gateways).
- Playtests from the root with `--world xeen`, each **4 of 4** (`output/studio_cal/dd23/four.out`, logs in
  `output/studio_cal/dd23/a7_xrun/`): `playtest.yml` (82 steps: the slope, the bone ledge and its pack, the perch hall,
  the ramp up, the ledge walk, the question No then Yes, the five rocks broken, a foot's else text, the glass once and
  its else text, the hoard, save and load with the rocks still broken, down the rock steps and the gallery to the
  mouth), `playtest_hostility.yml` (20), `playtest_exit.yml` (14: out to D4, the landing measured).
- Pictures `output/studio_cal/dd23/shots/` (sheets `shots_0.jpg`, `shots_1.jpg`), unbaked (the lead bakes). Looked at:
  the cave reads as one dark rock family; the perches, the pillars, the steps, the snow drift and the straw nest show.
  Fixed after them: the crack's chimney lowered from 2,944 to 2,304 (the sky showed as a sliver); not shot again
  (one tour per session).

- **From `assets_dev` with A2's row 9176 (2026-11-20, tenth session, binaries of merge point 18):** first the
  installed build, then rebuilt with `xdcraglt` (L4 differs by that surface alone; build 0 warnings, audit 0/0),
  installed with its bake: `playtest.yml` (82), `playtest_hostility.yml` (20), `playtest_exit.yml` (14) 4 of 4 each,
  both times (`output/studio_cal/a7/s10_rows_dd23.out`, `s10_crag_dd23.out`). The scratch root
  `output/studio_cal/dd23/root` is deleted (later builds go through `output/studio_cal/a7/root_s6`). Pictures of the
  mouth, baked: `output/studio_cal/dd23/s10_look/sheet.jpg`.

## Exceptions

- **Doors:** 0 doors against the S band's 3-8: a natural cave with D4's open mouth (D-39 (4), XD-26's caves the
  precedent).
- Texture fit exceptions: none (audit clean).
- Dressing exceptions: none (audit clean; one stalagmite moved off the walking line between the slope's and the
  ramp's openings).

## Words needed

- **One event, several clicked sources:** `sources` is for steps only, so the question is ten events (five rocks,
  five feet) written by gen.py from one template.
- **A destructible that leaves rubble:** a broken rock's faces vanish; the dust heap is a separate low platform under
  each rock from the start (its foot).

## Decided

- **D-45 (1), 2026-11-20:** the lair keeps 7d07's dark brown-black cave rock `c2b` and rock floor `cfb1` (D-39's "grey"
  misdescribed 7d07; it reads apart from XD-26 and matches D4's dark rock slope).
- **D-45 (2), 2026-11-20:** the mouth's exit shows a new Darkside crag view, `xdcraglt` (1 of S's 4 new textures):
  from high in a cave mouth, bare dark crags with snow in their clefts, a grey lake far below, dark ridges into haze,
  the dim amber-grey sky of `xeen_darkside_day`, no trees. Codex project
  `level_generation/textures_xeen/a7_dd23_craglt/` (references: two game pictures of D4 from the lair's landing under
  `xeen_darkside_day`, `pics/`, and 7d07's `c2b`; one version, finished at gain 0.45, logical 256 × 256 drawn at the
  face's 384 × 320; master in `assets_source/worlds/xeen/textures_x4/`). It read as meant, so `xddaylt` (the
  fallback) is not used here. A6 registers it in `source/textures.yml`; usable on any other high mountain cave of the
  Darkside. (D4 round the landing itself shows grass and trees; the picture is the decider's view from the crag.)

## For the user

- Arrive in the mouth facing up the cave; the perch hall's gargoyles on their perches, the upper ledge over the hall
  (step off its lip: a drop of 640), the rock ramp behind the west wall.
- In the roost, look up through the crack at the Darkside's day, the snow under it; click a roosting rock and answer
  Yes: all five crumble to dust. Leave and come back: they stay dust.
- The nest of shiny things: Caleb's glass and the hoard.

## chest.front (2026-11-22, lane A7 twenty-seventh session)

The build's `chest.front` warning (merge point 41: an indoor chest's `facing` is its long axis, its front 90 degrees
anticlockwise of it): the chest(s) it named turned 180 degrees in place, back to the wall, front to the room.
Installed with the bake; build warnings and audit as before.

## D-89 cave shape, identity and name test (2026-11-22, lane A7 28th-29th sessions)

Shared pass `tools/xeen/cave_shape.py` (corners cut where no other room, object or numbered wall is near, `rough` walls,
floor points that rise and fall with everything standing pinned level, vaulted roofs), called from this map's generator
after L4 is written; `identity:` in project.yml. Metrics are `oymap metrics`' cave_shape (floor uneven share, ceiling
spread, rough wall share; the audit's numbers 0.30 / 80 / 0.18). `tools/xeen/check_identity.py <key>` checks the family
share and the shape of the installed map.

- Metrics before -> after (floor / ceiling spread / rough): 0.16 / 73 / 0.05 -> 0.35 / 138 / 0.29; family 7d07 99 %.
- No change in s29.
- Name test (arrival, first fight room, signature room), engine captures from `assets_dev` in
  `output/studio_cal/a7/s29/names/dd23/shots/`  (01-1_arrival.png, 02-2_perch_hall.png, 03-3_roost.png); all eight maps
  on one sheet `output/studio_cal/a7/s29/names/names_sheet.jpg`. Reads as named: the mouth on dark rock with gargoyles
  beyond, the perch hall's gargoyles and droppings, the Overlord on the roost's highest rock.

## Mouth exit kept clear of rough rock (2026-11-23, agent:xeen-xd05-exit)

The rough wall behind this map's exit stood in front of its black face (no click reached it: the XD-05 Discord report,
`tools/xeen/check_exits.py` `exits.hidden`). `tools/xeen/cave_shape.py` `flat_behind_panels` now gives the exit's
wall a flat panel under it (the generator writes it); rebuilt, installed and baked; all playtests pass. See XD-05's
NOTES.md, same date.
