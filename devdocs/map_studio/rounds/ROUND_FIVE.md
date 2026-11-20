# Round five of the rebuild loop (2026-11-13, night): brief for every rebuild agent

You are a rebuild agent in the Map Studio's self-correcting loop (repository `/home/pjasicek/github/OpenYAMM`). Your
task message names your map, its key, its world and its own targets. This file holds what is the same for all seven.

Read first, fully: `devdocs/map_studio/REBUILD_PROCEDURE.md` (rules, tools, what NOTES.md holds);
`devdocs/map_studio/S3.md` from "Round four" to "WebAssembly" (what round four left, what was built since); your own
`devdocs/map_studio/briefs/<key>/L4/NOTES.md`, above all its "Round four" section and its gaps still open. Every
field is described by `openyamm-studio/build/oymap schema rooms|objects|wiring|project|common`; one of each feature
is in `openyamm-studio/examples/shapes_gallery/` (its pictures: `output/studio_shapes/shots/`, 84 to 100 are the
newest); `openyamm-studio/README.md`, "Words added since 2026-11-12", lists the new words.

## What this round is for

The seven rebuilds are 94.7 to 99.4 % alike in shape and textures, and the measure sees nothing else. This round is
first about **what is in the rooms and what happens there**, second about the last shapes that now have words, third
about undoing the compromises round four had to make.

1. **Contents.** Every monster the original places at a fixed spot and every item it leaves lying, at the original's
   place: read them from the original's scene file (`assets_dev/worlds/<world>/maps/<map stem>.scene.yml`,
   `initial_state.actors` and `sprite_objects`) and from `oymap export`; say them with objects.yml `monsters[]`
   (`monster` by name or number, `at`, `facing`, `hostile`, `group`, `immobile`, `hp`, `name`) and `items[]`.
   Every placeholder in your project that stood for a monster, an item, a clicked block, a chest or lever on a
   moving part becomes the real thing. Spawn points stay spawn points.
2. **Behaviour.** Each of the original's events once more against yours (`oymap flow <map> --world <w> --assets
   assets_dev`, and `--event <n>`): the same thing under the same condition. New words: conditions `kills` (a
   group, a placed monster, all) and `lua` (a Lua test that guards sets and effects); effects `lights_on` and
   `lights_off` (lights get ids; `lights[].on: false` starts one dark; `pulse`); a platform or wall panel with an
   `id` as a click source; a step event on a mover; `doors[].secret`; a level or platform that is seen but not
   solid (`solid: false`) or solid but not seen (`visible: false`); ladders; placed sounds.
3. **Shapes that now have words.** A hanging slab whose underside slopes with its top (`platforms[].thickness`
   with `top_slope`) and `bottom_surface`; `floor_surfaces` and `ceiling_surfaces` (a surface for the steep parts
   or a region of an uneven floor or roof); mouths that follow both rooms' uneven floors and roofs (a raking
   sill; `height: full` point by point; a shaped mouth in strips; `trim_to_wall`); an arch as high as a vault's
   end; a flight that ends in a doorway (`to_height` on a wall); a mover that passes into the ceiling or a wall
   at one end; `movers[].parts[]` (several blocks as one mover) and `floor_height`; `chests[].rides`,
   `chests[].top_surface`; `switches[].block` and `side`; a level over an uneven floor.
4. **Warnings to answer.** The build now warns where an opening could have taken another pair of walls (pin it
   with `from_wall`/`to_wall`), where a mover stands over several floors (`floor_height`), and of rules that
   changed (`project.yml` `migrated`, once the project is right for the new rule). End the round with no warning
   you could have answered.
5. **Compromises of round four** named in your task message: undo each one whose word now exists.

## Rules that bind (with the procedure's)

- The project files are the source. No `gen/` script is run. A helper that edits many things at once is allowed
  if every number it writes is measured from the original and you check its whole diff; keep it in your scratch
  folder and say in NOTES.md what was scripted.
- **A wrong shape that measures better is forbidden.** Every change makes the rebuild more like the original as
  measured from the original's files, not merely higher in score. Monsters, items and events do not move the
  score at all: they are checked by `oymap audit`, `solve`, the playtest and your own reading of the original.
- Uneven floors and roofs keep to the point budget of the procedure; name rooms that take the original's points
  one for one.
- Work only in `devdocs/map_studio/briefs/<key>/L4/` and `output/studio_cal/<key>/`. Copy the project as it stands
  to `output/studio_cal/<key>/r5_backup/` before your first edit. Do not build the studio or the game: use
  `openyamm-studio/build/oymap` and `build/game/openyamm` as they are (other sessions rebuild the game now and
  then: if a run fails because the binary is being written, wait a minute and run again). No git command that
  changes anything. `rm` only with a literal path, after `ls`, as its own command. `/tmp` is not durable.
- Build with `--out output/studio_cal/<key>/build`. Run `oymap fmt` before every check. Build repros from copies
  with `--out` into scratch (a build writes `ids.lock.yml` into the folder it reads).
- Game runs: headless scenarios as the procedure says; desktop runs (`ingame_compare.py`, always with
  `--root output/studio_cal/<key>/root`) with `SDL_AUDIODRIVER=dummy` in front. Wait on exact PIDs, never on
  `pgrep -f <text>`.
- **The playtest must not depend on chance.** Run it at least four times at the end. A walk that a wandering
  monster can block takes `clear_hostiles`; a step that needs room in the packs makes room first (the Forge's
  `playtest.yml` shows both, with the lead's comments); placed hostile monsters will attack the party on its
  walk: the walk deals with them as a player would, and asserts what a kill should set.

## Order of work

Measure where it stands (`oymap compare <map> --world <world> --with devdocs/map_studio/briefs/<key>/L4 --assets
assets_dev --out output/studio_cal/<key>/compare_r5_start`). Then contents, behaviour, shapes, warnings, compromises,
in that order; re-measure after each group of shape changes. Keep every reachable room reached and `oymap solve` in
the original's order; extend the playtest over what you add (a placed monster is met, an item is picked up, a
clicked block answers, a light goes on). Take same-camera game pairs where you changed what is seen, and a few
pictures of rooms with their monsters and items; look at them yourself.

Then add "Round five" to NOTES.md: scores at start and end (shape, textures); how many of the original's fixed
monsters and lying items are placed, and which are not and why; the events table brought up to date (same,
differs how, missing why); playtest steps and its result over four runs; what changed; which new features worked
and which were refused (exact message, a small repro under `output/studio_cal/<key>/repro/<name>/`); compromises
undone and those that stay; gaps still open most harmful first (where, and the field that would say it); tool
defects with the command that shows them.

## Your final message

It is read by the lead session, not by a person. Give: scores (start, end; shape; textures); monsters and items
placed of how many; events that match of how many; the playtest's result over four runs; the three changes that
mattered most; every refused feature with its repro path; compromises undone and left; the gaps still open in
order; any place where score and the original pulled apart and what you did. Plain facts, no padding.
