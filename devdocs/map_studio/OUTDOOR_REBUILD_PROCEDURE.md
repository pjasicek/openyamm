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
  measured from the original, its whole diff checked, kept in your scratch folder, named in NOTES.md.
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

## NOTES.md

Scores at start and end, by part; what changed; what was scripted; **gaps** (everything the vocabulary could not say,
most harmful first, each with where it occurs, what you did instead and the field that would say it); **tool
defects** with the command that shows them (a small repro project under `output/studio_cal/<key>/repro/<name>/`);
what you were unsure of in the original.
