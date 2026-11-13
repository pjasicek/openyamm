# Rebuilding a shipped dungeon as a Map Studio project (procedure for rebuild agents)

Purpose: a rebuild is a test of the studio's vocabulary, not a copy for its own sake. If an agent can describe a
known dungeon in project files and the build comes out like the original, the same means will make new dungeons as
good. Where the vocabulary cannot say something, that is the finding. The user decided (2026-11-12) that these
rebuilds run as a self-correcting loop: build, compare with the original by tool, fix, repeat, without a person
pointing at differences.

Read first: `openyamm-studio/README.md`; `devdocs/map_studio/S3.md` (section "State at the end of 2026-11-12": what
exists, what does not, the mistakes made); the worked rebuild `devdocs/map_studio/briefs/mm7_7d06/L4/` (Temple of
the Moon: rooms.yml, objects.yml, wiring.yml, project.yml) and the test map `openyamm-studio/examples/shapes_gallery/`
(one of every room feature). Every field is described in its schema: `openyamm-studio/build/oymap schema rooms`
(also `objects`, `wiring`, `project`, `common`).

## What you produce

In `devdocs/map_studio/briefs/<key>/L4/`: `project.yml`, `rooms.yml`, `objects.yml`, `wiring.yml` (and
`ids.lock.yml`, which the build writes; keep it), plus `NOTES.md` (below). Work only in that folder and in
`output/studio_cal/<key>/` for scratch data and pictures. Give `project.yml` a `map_stats` block with an `id` of your
own (9700 + the number given in your task) and `reference: <the original map file>`.

## Rules

- **The original's frame.** Draw in the original map's own x, y and z, so the two maps can be laid over each other
  and compared point by point. Not on a 512 grid.
- **Measured shapes, not traces.** Read the original with the tools (below) and describe it: a room is its outline
  with as many points as its shape needs (a rectangle 4, a cave 8 to 30), its floor and ceiling, and its features.
  Do not copy vertex lists of the original's faces into outlines: if a room needs more than about 30 points, it is
  several rooms or it needs a feature the vocabulary lacks. Positions of doors, chests, torches and spawns may be
  taken exactly.
- **Uneven floors and roofs** (`floor_points`, `ceiling_points`): give a height where the surface changes slope,
  read from the original; not every vertex of the original's faces. A cave's floor rarely needs more than about
  25 points and its roof about 40; a room that needs more is several rooms. Where you did take the original's
  own points one for one, say so for that room in NOTES.md.
- **A script may write the project files** (the user's decision, 2026-11-12), for a first shell or for one edit
  over many rooms. It is held to the same rule as a hand: rooms as their shapes need them, numbers measured from the
  original. Keep it in `L4/gen/` (a first shell) or your scratch folder (a one-off edit) and check its whole diff.
  Once a project has hand edits, the files are the source: a generator that would write them afresh is not run
  again. Say in NOTES.md what was scripted.
- **The original's own textures**, by name, wherever a surface of the rebuild stands for one of the original's
  (`oymap metrics` lists them by area; `oymap assets <name>` gives sizes).
- **Say it with the vocabulary**; where it cannot be said, do the nearest honest thing, put what is missing into a
  `placeholders` entry or a `notes` field, and list it in NOTES.md. Do not fake a shape with a trick that will have
  to be undone (the Temple's first nave used wedge rooms and loose treads; all of it was thrown away).
- **Do not edit** anything outside your two folders. Do not build the studio or the game (use
  `openyamm-studio/build/oymap` and `build/game/openyamm` as they are; if a command fails because the binary is
  being rebuilt, wait a minute). No git commands that change anything. No `rm` with wildcards or variables.
- Run `oymap fmt <folder>` before every check: project files are kept in canonical form.

## What the measure does not see (the user's walk through Gharik's Forge, 2026-11-13)

The Forge measured 99.6 % and its playtest passed every run, and the user still found, in one walk: levers of the
wrong kind (the original's are small 3D handles that move; the studio built flat plates), a lever whose picture did
not flip back, chests textured wrongly (the original lays a left end, a middle and a right end on front and top),
things that stood under a lift instead of on it, and faces flickering in one plane. `oymap compare` looks at walls,
floors and ceilings from the floor; a playtest checks that events run. Neither sees what the player sees at the
things he uses. So, in every round and every new dungeon:

- **Every interactive thing takes the original's form, not the studio's default:** levers, buttons, chests, doors,
  clicked panels and blocks. Read its faces in the original (`oymap export`: textures, sizes, which door record moves
  them) before you write it, and say in NOTES.md for each kind what the original has and what you built.
- **Look at every kind of interactive thing in the game,** in a picture from where a player uses it, before and
  after it is used (a lever pulled and pulled back, a chest from above, a door half open, a lift at the top and the
  bottom with what stands on it). Not only at the measure's worst places.
- **Things over moving parts:** check in the game that what stands on a lift, bridge or deck is on it at the start.
- **Where the party stands high:** take a picture from the top of every platform, flight, ledge and mover the party
  can stand on, looking round. A top that stands up into the room above puts the party's eye in another room, and
  the view goes black (the Abandoned Temple's arrival, round six); the measure scores it as perfect.
- **Flicker:** look for faces in one plane over each other near doors, movers and blocks; the build warns of them
  once the check exists.
- **Tools for this (since the eighth merge, 2026-11-13):** `oymap things <map|project>` lists every interactive thing
  (doors, levers, buttons, plates, chests, exits, teleports, clicked panels and decorations) with its textures, what
  it changes and where a player stands to use it; run it on the original and the rebuild and compare the lists.
  `python3 openyamm-studio/calibration/things_shots.py` takes a picture of each from there, before use, after one
  use and after a second. Switches take `kind: lever|button` (the originals' 3D handles and pushed blocks; `plate`
  only where the original is a flat plate) and chests `kind: ch1..ch5|7gt002|gt002|ch001..ch006`. `oymap build`
  warns of faces in one plane over each other (`geometry.coplanar` in `audit`): fix each the project causes, and
  say in NOTES.md which ones the original has too.
- A map is not done when it measures well and its playtest passes; it is done when a person could play it without
  meeting a thing that looks or behaves unlike the original.

## Textures for a new dungeon (the user's look at XD-01, 2026-11-13)

A rebuild takes the original's own textures. A new dungeon has no original, and XD-01 showed what goes wrong: its
agent picked 50 textures one by one by name from 23 shipped maps of three worlds, 23 of them from no shipped dungeon at
all (ship and outdoor woods: the user saw ship windows inside a warehouse). The user: reuse shipped textures where they
fit well, generate new fitting ones where nothing fits, and "avoid making it a Frankenstein's monster". So:

- **One family per area.** Build each area (a wing, a level, a cave system) from the set of ONE shipped dungeon whose
  purpose fits (a warehouse from a wooden pirate hold, a mine from a mine, a dwarven hall from a hall), and keep
  areas few. Say in NOTES.md which shipped map each area's set comes from. The MM8 pirate maps (Pirate Outpost
  `d06.blv` and its neighbours) show a coherent wooden set (wainscot `t66b01`, planks `t66floor`, hall brick
  `t66c01a`, posts `t66abc10a`, flagstones `t66flr2`, roof `t66roof`, doors `t66b03l`/`r`); the user named it.
  A family is not a list of names: look at how its map lays each one (`t66e01s1`, the most used, is the hull of the
  moored boat, not a wall; XD-01's texture pass found it).
- **Look up where a texture comes from** before using it: `python3 openyamm-studio/calibration/texture_use.py
  <texture>` (the shipped dungeons that use it), `--map <world/map.blv>` (a dungeon's set), `--project <folder>`
  (every texture of a project with its source; textures from no shipped dungeon are flagged). A texture no shipped
  dungeon uses needs a reason in NOTES.md.
- **Look at each texture as a whole picture in the game** (a wall of it), for motifs that betray where it comes from:
  windows, portholes, signs, symbols of another place.
- **Where nothing shipped fits,** do not borrow a misfit: list it in NOTES.md under "textures to generate" (what it
  shows, size, where it goes) and use the nearest coherent stand-in meanwhile. The repository can generate textures
  (`level_generation/textures_x4/PLAYBOOK.md` is the pipeline for upscaled ones; new ones are a separate request to
  the user).

## Tools

```
O=openyamm-studio/build/oymap ; A=assets_dev
$O export assets_dev/worlds/<world>/maps/<map> --world <world> --assets $A --pretty --out x.json
                                   # every vertex, face, sector, light, spawn; with --world and --assets also `doors`
                                   # (each moving part: direction, travel, speeds, its faces and where they stand)
$O audit|metrics|solve|flow <map> --world <world> --assets $A [--reach] [--json]   # the original, as the game reads it
$O render <map> --world <world> --assets $A --out x.png --view plan|iso            # labelled picture (look at it)
$O assets <word> --assets $A --world <world> [--kind texture|decoration]
$O script-reference --assets $A --world <world>                                    # what a script may call
$O validate <L4> --assets $A ; $O build <L4> --assets $A --out output/studio_cal/<key>/build [--dry-run]
                                   # always with --out: without it the build lands in the brief
$O audit|metrics|solve|flow|render|probe <L4> --assets $A ...                      # the rebuild, built privately
python3 openyamm-studio/calibration/compare.py <L4> openyamm-studio/calibration/originals/<key>.metrics.json
$O compare <map> --world <world> --with <L4> --assets $A --out output/studio_cal/<key>/compare   # see below
```

`oymap compare` is the loop's measure (it may not exist yet when you start: check `$O compare`; until it does, use
renders, `compare.py` and probes, and start using it as soon as it appears). It stands at points all over the
original's floors, looks in 50 directions in both maps, and reports where the rebuild's walls, floors, ceilings and
textures differ, with the worst places named. Its `shots.yml` feeds
`python3 openyamm-studio/calibration/ingame_compare.py <L4> <world> <map> <shots.yml> <out folder>`, which takes
same-camera pictures of both maps in the game with a difference sheet for each pair. Look at those sheets yourself.

MM7 map files hold no usable light radius or colour (every light reads radius 0, colour 31,0,0, brightness 31: that
is the file, the game reads the same); take positions from the export and give the rebuild's lights a radius by eye.
`solve` and `audit --reach` ride moving floors (lifts, sliding bridges) since 2026-11-12.

To play the rebuild: `$O install <L4> --build output/studio_cal/<key>/build --mount output/studio_cal/<key>/mount
--assets $A`, then a headless scenario
with `build/game/openyamm --asset-root $A --extra-mount output/studio_cal/<key>/mount --world <world>
--headless-run-scenario <file> --scenario-no-color`, run from `output/studio_cal/<key>/run/` (form:
`devdocs/map_studio/briefs/mm7_7d06/L4/playtest.yml` or `openyamm-studio/examples/shapes_gallery/playtest.yml`).

## Order of work

1. **Read the original**: audit, solve (the order it opens up), metrics, the plan and iso renders, then the export
   for measurements. Write down the room list with what each room is.
2. **Shell**: rooms, openings, levels, stairs, in the original's frame. Check after every few rooms: `validate`,
   `render` beside the original's, `audit --reach`. Every room reached, the same way the original connects.
3. **Compare and fix the shell**: `oymap compare`; fix the worst places; repeat until the geometry score stops
   rising or what is left needs a feature that does not exist.
4. **Surfaces**: themes with the original's textures, bands, per-wall surfaces. `compare`'s texture score.
5. **Objects and wiring**: start, doors (the original's door records: which are real doors, which are moving walls,
   buttons, lifts), chests, spawns with the original's slots, lights or torches, switches, events (read each
   handler with `flow --event`; use presets, conditions and effects; a script only where no preset fits). `solve`
   must open the rebuild in the same order as the original.
6. **Play it**: a scenario that walks the critical path and uses every mechanism.
7. **Pictures**: `ingame_compare` at the comparison's worst places; look; fix what is yours to fix.

Stop when another round changes little. A rebuild is never finished; say where it stands.

## NOTES.md (the product, as much as the project)

- The scores: `compare`'s totals at the start of each round and at the end; `compare.py`'s line; rooms reached;
  whether the playtest passes.
- **Gaps**: everything the vocabulary could not say, most harmful first, each with where it occurs in this map, what
  you did instead, and what field would have said it. Be exact: "a floor opening onto the room below (the reactor
  shaft, 512 square, between level 2 and level 1)", not "vertical connections".
- **Tool defects**: every wrong result, crash, misleading message or check that should exist, with the command that
  shows it.
- What you were unsure of in the original (a room you could not read, a mechanism you did not understand).
