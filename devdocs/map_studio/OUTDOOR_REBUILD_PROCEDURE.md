# Rebuilding a shipped outdoor map as a Map Studio project (procedure for outdoor rebuild agents)

Purpose: as for dungeons ([REBUILD_PROCEDURE.md](REBUILD_PROCEDURE.md)). A rebuild tests the outdoor vocabulary: if a
known map can be described in a sketch and the build comes out like the original, the same means will make new maps.
Where the vocabulary cannot say something, that is the finding. The loop is: build, compare with the original by tool,
fix the sketch, repeat, without a person pointing at differences.

Read first: `openyamm-studio/README.md`; `devdocs/map_studio/S3.md` from "Second code batch merged" (its Outdoor
bullet) to the end of the outdoor paragraphs that follow; `openyamm-studio/build/oymap schema sketch` (every field is
described there; also `schema atmosphere`, `schema project`); the first batches' scratch folders
`output/studio_s4b/` and `output/studio_s4c/` (read only: analyses of the originals in `analysis/`, the scripts that
wrote the first sketches in `gen/`, game pairs).

## What you produce

In `devdocs/map_studio/briefs/<key>/L4/`: `project.yml`, `sketch.yml`, `plan.yml`, `atmosphere.yml` where needed,
`ids.lock.yml` (the build writes it; keep it), `playtest.yml` (the walk), and `NOTES.md`. Work only in that folder and
in `output/studio_cal/<key>/` for scratch data, mounts, roots and pictures.

The L4 you start from was written from the original by scripts (a 32 x 32 grid of spot heights, road beds, each
building's parts and sizes, where monsters and people stand). From now on the files are the source: those scripts are
not run again. What the scripts could not say or got wrong is yours to find with the measure.

## Rules

- **The original's frame.** The sketch is in terrain cells of the original's 128 x 128 grid.
- **Described, not traced.** Heights are a coarse grid of spot heights (at most 32 x 32), height points where the land
  has a peak, a hollow or a ledge the grid misses, and cliff lines where it breaks; never the original's 128 x 128
  height field. A building is its kind, parts, sizes, roof and textures as measured, never its model's vertices.
  Decorations are scatter by area, kind and count (their places inside an area are the build's), or single placed
  things where the original has a landmark. Positions of doors, chests, spawn points, people and exits may be taken
  exactly.
- **The original's own textures and tiles**, by name.
- **Say it with the vocabulary**; where it cannot be said, do the nearest honest thing, leave a note on the object and
  list it in NOTES.md. Do not fake a form with another (a ship as a house).
- **A wrong shape that measures better is forbidden.** Every change makes the map more like the original as measured
  from the original's export. If the honest form scores lower, keep it and say so.
- A script may write parts of the sketch (see REBUILD_PROCEDURE.md, "A script may write the project files"): numbers
  measured from the original, its whole diff checked, kept in your scratch folder, named in NOTES.md. After every
  run, `oymap record $P --author agent:<your name> --label "<what it wrote>"`, so the history names you.
- Do not edit anything outside your two folders. Do not build the studio or the game (`openyamm-studio/build/oymap`
  and `build/game/openyamm` as they are; another session rebuilds the game now and then: if a run fails because the
  binary is being written, wait a minute). Write nothing into `assets_dev` (files in a `cp -al` root are hard links to
  it: never edit one in place). No git command that changes anything. `rm` only with a literal path, after `ls`, as
  its own command. `/tmp` is not durable.
- Run `oymap fmt <folder>` before every check.

## Tools

```
O=openyamm-studio/build/oymap ; A=assets_dev ; K=<key> ; P=devdocs/map_studio/briefs/$K/L4 ; C=output/studio_cal/$K
$O export assets_dev/worlds/<world>/maps/<map> --pretty --out x.json      # heights, tiles, models, decorations, spawns
$O audit|metrics|render <map> --world <world> --assets $A                  # the original as the game reads it
$O validate $P --assets $A                                                 # a dry build: refuses what the build would
$O build $P --assets $A --out $C/build                                     # always with --out
$O compare <map> --world <world> --with $P --assets $A --out $C/compare    # the loop's measure (below)
$O render-sketch $P --out x.png ; $O render $P --assets $A --out x.png     # the sketch as a plan; the built map
$O install $P --build $C/build --mount $C/mount --assets $A                # to play it headless
$O record $P --author agent:<you> --label "<what>"                         # after a script wrote the sketch
$O pins list|claim|resolve|reply|tour $P ...                               # the user's pins (below)
python3 openyamm-studio/calibration/outdoor_materials.py $P --root $C/root # the terrain material file, for pictures
python3 openyamm-studio/calibration/outdoor_ingame.py $P <world> <map> <shots.yml> $C/ingame --root $C/root
                                                                           # same camera in both maps, difference sheets
```

`oymap compare` reads both maps on the 128 x 128 grid in ten parts (heights, relief, cliffs, water, ground, roads,
buildings, decorations, spawns, events), gives each of the 64 regions a score, names the worst with what differs, and
writes `report.json`, `differences.json` (every difference), four pictures and a `shots.yml` of the worst places.
Work from `differences.json`. Decorations are paired with the original's, nearest first within 16 cells, by kind
and by any kind (since 2026-11-13; before that only their number per region counted): a clump scores as it
stands, wherever region borders fall.

To play: a headless scenario from `$C/run/` with `build/game/openyamm --asset-root $A --extra-mount $C/mount --world
<world> --headless-run-scenario $P/playtest.yml --scenario-no-color`, `SDL_AUDIODRIVER=dummy` in front. For pictures a
scratch root (`cp -al assets_dev $C/root` once, then `oymap install $P --build $C/build --root $C/root`), desktop runs
through the two calibration scripts, HUD off. Wait on exact PIDs, never on `pgrep -f`.

## Order of work

1. Measure where it stands; read the parts and the worst regions.
2. Land and water: what the grid misses (peaks, ledges, crisp banks), water outlines, shores.
3. Ground kinds and roads.
4. Buildings: every building of the original present, of the right kind, parts, height and roof, door where the
   original's is and leading where it leads; then the things that are not houses.
5. Events, spawn areas, people, chests, exits and arrivals.
6. Play it: the walk opens houses and chests through what was built and leaves and returns by an edge.
7. Pictures at the measure's worst places and in the town; look; fix what is yours to fix.

Stop when another pass changes little or what is left needs a word that does not exist.

## Answering pins (S5a1, 2026-11-14)

The user's `pin <text>` notes from the game reach outdoor maps as they reach dungeons: follow REBUILD_PROCEDURE.md,
"Answering pins" (import, list, claim, fix in the project, `pins tour`, the game's after picture, resolve with what
changed; only the user accepts or reopens; pins are not the source and never edited by hand). Outdoors:

- The pin's pose is the party's feet on the land as `loc` gives it; a tour at that pose is applied exactly, airborne
  too. Install the fixed build into your scratch root (`oymap install $P --build $C/build --root $C/root`) and write
  the terrain material file there first (`calibration/outdoor_materials.py $P --root $C/root`), or the game refuses
  the map.
- A pin on a building names what is wrong with it; answer with the building's picture from the pin's pose and, where
  the fix moved it, the per-building shot (`calibration/building_shots.py`) beside the original's.
- Outdoor projects keep every entry of `ids.lock.yml` (an outdoor build never dropped one); `oymap lock prune` leaves
  them and says so.

## NOTES.md

Scores at start and end, by part; what changed; what was scripted; **gaps** (everything the vocabulary could not say,
most harmful first, each with where it occurs, what you did instead and the field that would say it); **tool
defects** with the command that shows them (a small repro project under `output/studio_cal/<key>/repro/<name>/`);
what you were unsure of in the original.


## Judged by eye against shipped towns (the user on Vertigo Meadows, 2026-11-13)

A new outdoor map built by rules came out regular and empty: one house kind in rows, empty plots, houses without paths
to their doors and a road under one, walls as plain extruded rectangles, almost no trees or flowers in town, road
rips, no waterfall where water met the rim, small evenly spaced monster groups, a thin dead forest. The user: an agent
should judge "not mathematically" but by what it feels from screenshots, compared with similar MM7/MM8 towns. So for
every new outdoor map: before building, and again before the user plays it, a reviewer agent takes the same views of
the map and of comparable shipped towns and writes what makes the shipped ones feel alive and what the new map
lacks (house kinds mixed, placement irregular, a path to every door, gardens and props, real walls with towers and
gates, waterfalls, monster groups as the shipped maps size and space them); the builder works from that review.


## The user's walks feed the studio, not just the map (2026-11-13)

Every place the user sends from a walk is fixed in three steps: in the project, with the original's shapes; as a
word or defect on `rounds/NEXT_CODE_BATCH.md` when the studio could not say it; and as a rule in this procedure
when it is a kind of mistake (z-fighting, doors in another town's style, asymmetric fronts, buildings built into
the terrain). Calibration cases the user names (Shadowspire's dragon cave: a dungeon built into the terrain) get
their own measured section here.


## Buildings built into the terrain (measured on Shadowspire round three, 2026-11-13)

On the shipped maps a dungeon entrance in a hill is a hollow shell of model faces, not terrain carved round a door.
Measured on Shadowspire's Yaardrake's Cave (d49out_W/_W_1, 104 faces), Emerald Island's dragon cave and Temple of the
Moon entrance (DragonCave_E*, CaveFall*), and Regna's d34entrance_N and d47out_W:
- **The shell:** 40-60 large triangles, no floor, no back, textured in the ground's own tile texture (VOLTYL; 7dirttyl
  beside Cwb1 rock; Grastyl), so the mound reads as land. Water models (7wtrtyl) may run over it.
- **The mouth:** a tunnel 250-300 deep narrowing to one dark face (solid01/7solid01) with the enter event; every other
  face carries the hint ("A Cave"). The mouth's floor is the terrain.
- **The terrain:** flattened to exactly the shell's foot height under the mouth and the mound's front; it rises inside
  the shell so the shell's back and side edges lie on terrain nodes. Beyond the shell the hill goes on. Under the front
  the terrain need not rise at all (Regna: a shell to 1504 on flat land at 960).
- **The approach** may be a cliff (Yaardrake is reached from above).
- **The other kind** (the Mad Necromancer's Lab, d20out): a building sunk in a level pit of tar, its hall's back
  against a cliff, its walk slabs floating over the pit.

To rebuild: read the shell's faces and the terrain nodes under its footprint in the export; set the floor shelf and
the back-edge nodes exactly (`ridges` at the original's nodes); until `kind: cave_mouth` exists, take the shell as a
`kind: model`. Never stand a door frame on a smooth mound: that is Vertigo's "black door in a dirt frame". New maps
use the same form (Vertigo's dungeon doorways).


## Town feel (measured; 2026-11-13)

Before the user walks any outdoor map with a town, run `openyamm-studio/calibration/town_feel.py` on the built map and
bring every flagged figure inside the shipped range, or say why not; the rules are in `devdocs/map_studio/TOWN_FEEL.md`.
It overrides the earlier by-eye advice to turn houses: shipped houses face the compass axes; towns look irregular by
placement, setbacks, plot sizes and short road runs, and many sit on slopes.

## Tree spacing (measured)

Measured from the exported decorations of Deyja (7out05), Tularean Forest (7out04), Harmondale (7out02),
Shadowspire (out06), Murmurwoods (out07) and Mire of the Damned (outc3). Distances are in cells (512 units). Density
is per cell of the ground the trees stand on (cells within 2 of a tree). Evenness is Clark-Evans R: the mean
nearest-neighbour distance over that of a random scatter at the same density (1 = random, below 1 = clumped, above
1 = even).

| map | trees | nearest: median / 10th pct / least | per cell | R | trees within 2 cells: median / 90th pct | kinds mixed (unlike nearest pairs, observed / random) | rim / core nearest |
|---|--:|---|--:|--:|---|---|---|
| Deyja (dead, tree41/42) | 98 | 1.97 / 1.35 / 0.97 | 0.116 | 1.47 | 1 / 2 | 0.51 / 0.44 | 2.47 / 1.70 |
| Tularean Forest | 232 | 1.85 / 1.07 / 0.77 | 0.116 | 1.47 | 1 / 2 | 0.43 / 0.51 | 2.93 / 1.32 |
| Harmondale | 287 | 2.35 / 1.36 / 0.73 | 0.103 | 1.75 | 0 / 1 | 0.70 / 0.57 | 2.83 / 1.50 |
| Shadowspire (dead, tree28) | 84 | 5.51 / 3.25 / 2.38 | 0.081 | 3.48 | 0 / 0 | one kind | 5.5 / 5.5 |
| Murmurwoods, forests | 1480 | 1.63-1.85 / 0.82-1.31 / 0.12-1.0 | 0.15-0.20 | 1.37-1.42 | 1 / 2-4 | 0.91-1.00 / 0.75-0.89 | 1.8-2.2 / 1.4-1.75 |
| Mire of the Damned | 374 | 2.71 / 1.70 / 0.40 | 0.095 | 1.82 | 0 / 1 | 0.32 / 0.81 | 2.94 / 2.71 |
| X1 dead forest, pass two | 230 | 0.59 / 0.50 / 0.12 | 0.32 | 0.70 | 5 / 10 | 0.09 / 0.48 | 0.67 / 0.53 |
| X1 dead forest, now | 139 | 1.81 / 1.49 / 1.15 | 0.13 | 1.45 | 1 / 2 | 0.39 / 0.44 | 2.38 / 1.69 |

The rule:
- Shipped stands are even, never clumped: R 1.4-1.8 (3.5 for Shadowspire's lone dead trees). Each tree has 0-1
  others within 2 cells (at most 2-4 in the thickest forest). Nearest tree 1.6-2.7 cells (median), 1.0-1.7 (10th
  percentile), and almost never under 0.7 (Murmurwoods' few 0.12 pairs are drawn as one tree). Density
  0.08-0.12 trees a cell (0.15-0.20 in Murmurwoods' deep forests).
- Kinds are mixed tree by tree, not in patches of one kind: unlike nearest pairs about as often as chance.
- A stand thins at its rim: nearest-tree distance at the rim is 1.3-2 times the core's, over about the last 3 cells.
- Do not use `clusters` for a forest. It packs a clump at `spacing` (half a cell) and leaves bare ground between
  clumps, which is what Vertigo's dead forest showed. Use `clusters` only for small things meant to clump
  (flowers, bones, rocks). Draw a forest as one even throw over all its kinds at least 1.4 cells apart, with about
  1 in 10 at 1.0, 0.10-0.13 trees a cell, and the last 3 cells thinned to a third at the rim. X1 does this in
  `output/studio_cal/x1/tools/dress.py` `even_stand` (one entry of count 1 per tree) until the studio has the words
  below.

## Roads and rivers to neighbours run to the map edge

In every shipped map checked (MM7 Harmondale, Erathia, Tularean Forest, Deyja, Tatalia; MM8 Ravenshore, Alvar,
Shadowspire, Murmurwoods; MM6 New Sorpigal, Mire), a road that leads to a neighbour runs on through the travel
border to the terrain's last row or column. Its road tiles reach row/column 0-3 from the edge (0 in 11 of 14
roads). Rivers and sea that leave the map reach the edge too: 0-1 cells (Harmondale's southern river 4). Draw such
a road's and river's line to the edge cell (0 or 127/128), not to the travel point: the party never gets there,
but it sees the way go on. X1 had them stop 17 cells short. A road or river that ends at the world (Xeen's rim,
the waterfall) is not extended.

## Wild land density (measured)

Over each map's land inside the play bounds (cells 20-108):

| map | decorations / 100 land cells (trees, bushes, rocks, flowers, other) | land >3 cells from anything | >5 | widest bare stretch (radius) | relief: std of height in 8x8 cells (median / 90th pct) | tile kinds per 8x8 (median) | monster markers, nearest (median) |
|---|---|--:|--:|--:|---|--:|--:|
| Deyja | 3.5 (1.2, 2.1, 0.1, 0, 0.1) | 0.60 | 0.33 | 26 | 557 / 1219 | 9 | 3.0 |
| Tularean Forest | 7.4 (3.5, 1.7, 0.6, 1.5, 0.2) | 0.33 | 0.13 | 13 | 536 / 1125 | 12 | 3.1 |
| Harmondale | 6.7 (3.3, 0, 0.3, 2.9, 0.1) | 0.36 | 0.14 | 22 | 418 / 727 | 17 | 3.9 |
| Shadowspire | 5.0 (0.4 trees, 3.4 bones/posts, 1.0 rocks) | 0.60 | 0.33 | 23 | 531 / 911 | 11 | 4.3 |
| Murmurwoods | 8.3 (3.4 trees, 3.5 stumps, 1.1 rocks) | 0.42 | 0.26 | 16 | 256 / 736 | 9 | 4.3 |
| Mire of the Damned | 4.9 (4.3, 0, 0.5, 0, 0.1) | 0.28 | 0.07 | 15 | 131 / 816 | 18 | 4.5 |
| X1 pass two | 12.6 (6.4, 0.4, 0.8, 3.9, 1.0) | 0.33 | 0.14 | 13 | 45 / 334 | 10 | (camps) |
| X1 now | 12.9 (5.8, 0.5, 1.1, 4.5, 1.0) | 0.12 | 0.01 | 7 | 141 / 409 | 10 | (camps) |

The rule: a shipped map's wilds are never flat. Height varies 130-560 (median std) in every 8 x 8-cell window. They
hold 3.5-8.3 decorations per 100 land cells, half or more of them trees, and leave a third to a half of the land
more than 3 cells from anything. What fills the eye is relief and evenly spread trees, not count. X1 already had
more things than any shipped map and still read as empty, because its meadow floor was flat (45). Roll the wilds
(swells of a few hundred units over 15-20 cells, kept out of towns, doors and places). Spread trees evenly. Keep
open views where they are wanted. Place one small place (old camp, bones, stones, a camp of monsters) every 10-20
cells along a view.

## Town density (measured)

Buildings (BModels, not walls) in the town's footprint: the hull of its buildings clustered by gaps under 6 cells.

| town | buildings | footprint (cells) | per 100 cells | coverage | median building | gap to nearest (median) | per 10 road cells | services of doors |
|---|--:|--:|--:|--:|---|---|--:|--:|
| Harmondale | 40 | 523 | 7.6 | 0.21 | 556k (2.1 cells) | 338 | 10.5 | 65 % |
| Ravenshore | 100 | 1577 | 6.3 | 0.26 | 614k | 0 (joined) | 4.5 | 25 % |
| Erathia | 54 | 601 | 9.0 | 0.29 | 505k | 108 | 3.9 | 31 % |
| New Sorpigal | 51 | 462 | 11.0 | 0.19 | 262k | 135 | 7.5 | 52 % |
| Alvar | 54 | 1022 | 5.3 | 0.23 | 944k | 200 | 3.2 | 28 % |
| Tatalia | 48 | 526 | 9.1 | 0.45 | 642k | 0 (joined) | 9.1 | 32 % |
| Vertigo, pass two (all, no wall) | 43 | 715 | 6.0 | 0.11 | 313k | 541 | 5.5 | 44 % |
| Vertigo, now (all, no wall) | 54 | 988 | 5.5 | 0.11 | 420k | 527 | 6.0 | 44 % |
| Vertigo inside the walls | 23 | 182 | 12.6 | 0.23 | 313k | 396 | 7.7 | 50 % |
| Vertigo with walls and farm belt | 92 | 999 | 9.2 | 0.21 | 510k | 275 | 9.5 | 44 % |

The rule: shipped towns cover 0.19-0.45 of their footprint. They have 5-11 buildings per 100 cells, a median
building of 260k-950k square units (1-3.6 cells) and a median gap of 0-340 units: neighbours touch or stand a lane
apart. A town of 40-100 buildings has a quarter to two thirds of its doors as services. Vertigo inside its walls is
in range (0.23 coverage, 12.6 per 100 cells, a little loose at 396). Its outskirts are not: coverage 0.11 and gaps
of about 530. The creek (3 cells wide), the fields and the gardens inside the hull account for about 190 of its 988
cells. Pass one's 590k median footprint and 1,664 gap became 313k and 541 in pass two. They are now 420k and 527,
after 12 more homes and 4 enlarged ones.

### Words the studio's scatter lacks (proposed, exact)

- `spacing_group: <id>` on a scatter entry: entries with the same group keep `spacing` from each other's decorations,
  not only their own. Today `spacing` holds inside one entry (OutdoorPlaces.cpp `place`), so a stand drawn as one
  entry per kind overlaps itself.
- `kinds: {<decoration>: <weight>, ...}` instead of `decoration`: one even placement whose places take a kind
  chosen by weight, so kinds mix tree by tree.
- `close_share: <0..1>` with `close_spacing: <cells>`: that share of the decorations may stand `close_spacing` from
  a neighbour instead of `spacing` (shipped stands keep about 1 in 10 pairs at 0.7-1.0).
- `edge_thin: {width: <cells>, keep: <0..1>}`: within `width` of the outline the chance to keep a place falls
  linearly from 1 to `keep` at the outline (measured: rim gaps 1.3-2 times the core's over about 3 cells).
- Even placement itself: `place` draws uniform random places and refuses only those within `spacing`, which with
  the default half cell is a random (R about 1) scatter. Shipped stands have R 1.4-1.8. A
  `spacing` of about 0.6 / sqrt(density) gives that; the doc of `spacing` should say so.
- The build's warning `N of M decorations found no place` should name the entries.


## Every building pictured beside the original (the user on Castle Ironfist, 2026-11-14)

"Basically the buildings are the issue; take a screenshot in front of the buildings and compare; I can't take
screenshots of all the buildings for you while you can." Before the user walks a rebuild, run
`openyamm-studio/calibration/building_shots.py` (each building's doors and sides, rebuild beside original), look at
every pair and fix or name each difference. The user's walk is for what this misses, not for finding buildings.


## Dungeon entrances that read as entrances (the user on Vertigo, 2026-11-14)

Shipped towns never put a dungeon door as a frame on open ground. Measured (MM7 Erathia, Tatalia; MM6 New Sorpigal,
Free Haven; MM8 Ravenshore): a building of its own (Erathia's sewer house: planks over stone, black `7solid01` door;
Tatalia's wine cellar behind a poor house's door; Ravenshore's Merchant House), a stone porch against a hill (Free
Haven's sewers), a grated outfall in a bank or quay (Erathia's three pipes); outside towns a cave mouth or timbered
adit in a slope. MM7/MM8 title the click face "Enter <name>"; MM6 asks on the click.
Rules: put every way in into something (building, porch in a slope, bank, rock); a dark opening (`7solid01` or the
world's black door), barred for a grate, never a house door texture; torches either side (3D standing torch `dec06`)
and props of its kind (casks for a store, timber and spoil for a mine, skulls for a lair); title "Enter <name>"; keep
each click face where the dungeon's arrival expects it, nothing within 0.8 cell of its middle.

## Monsters by habitat (the user on Vertigo, 2026-11-14)

Orcs and goblins at their camps (a fire and a crate or tents within 1-3 cells); flying insects and amphibians over
marsh, ponds and creeks; undead in the dead forest and at graves; hill creatures in hills. A group in open meadow
with nothing round it reads as random. Keep `town_feel.py` inside its ranges (groups 47-88, wild group to nearest
403-2,433, spacing variation 0.46-2.08, nothing within 4,500 of a town door).

## Guards in towns (measured, 2026-11-14)

| Town | Guards | Townsfolk |
|---|--:|--:|
| Harmondale | 7 | 30 |
| New Sorpigal | 5 | 38 |
| Tatalia | 8 (bowmen) | 33 |
| Ravenshore | 20 (defenders) | 45 |
| Erathia | 0 | - |

About half walk the streets alone (300-2,000 from a house door, 2,000-4,700 from each other); the rest stand in pairs
350-850 apart at gates, bridges and the town's edges. One guard to every two to six townsfolk; a pair at each gate
and bridge, singles on the streets, never in a yard; peaceful, the world's town guard kind.


## Projects edited by hand (S5b1, 2026-11-15)

A project whose `project.yml` carries `edited_by_hand` (a person changed it in the studio, or someone ran
`oymap protect`) is changed only by operations (`oymap edit`, MCP `map_edit`, the request list), never by writing its
files. Read `hand_objects` in every edit result (objects a person changed last that your change touches) and leave
them alone unless the person asked. Never set or clear the mark: only a person does. Rename an object with the
`rename` operation, never by changing its id in the files (the lock and pins follow a rename).


## Land made by hand (S5b2, 2026-11-15)

`heights.strokes`, `heights.smooth`, `heights.patches` and `heights.hand_made` are a person's work: agents never write,
move or clear them, and never set `hand_made` (refused on rebuilds anyway). On land a person shaped, read heights
with `view.terrain_query` (height and slope at points, or a profile) rather than reconstructing them from the words.
