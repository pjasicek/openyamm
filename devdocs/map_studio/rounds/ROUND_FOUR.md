# Round four of the rebuild loop (2026-11-12, night): brief for every rebuild agent

You are a rebuild agent in the Map Studio's self-correcting loop (repository `/home/pjasicek/github/OpenYAMM`). Your
task message names your map, its key, its world and its own targets. This file holds what is the same for all seven.

Read first, fully: `devdocs/map_studio/REBUILD_PROCEDURE.md` (rules, tools, what NOTES.md holds);
`devdocs/map_studio/S3.md` from "Round three merged" to "WebAssembly" (what exists since your map's last round,
measured sections, what the originals' cave floors are); your own `devdocs/map_studio/briefs/<key>/L4/NOTES.md`,
above all its "Round three" section and its list of gaps still open. Every field is described by
`openyamm-studio/build/oymap schema rooms|objects|wiring`; one of each feature is in
`openyamm-studio/examples/shapes_gallery/` (its pictures: `output/studio_shapes/shots/`, 63 to 83 are the new ones).

## New since round three (use what the original has, nothing for its own sake)

- **Tunnels.** A `path` room takes a `section` (its cross-section as an outline `[across, up]`, floor first), with
  surfaces for `floor`, `lower`, `wall`, `upper`, `ceiling` and square ends (`start`, `end`); an opening
  `shape: section` is the tunnel's mouth (no lintel, no jambs), also tunnel to tunnel; path points may be
  `[x, y, z]` (a height at each point: one room for a tunnel whose grade changes); a climbing path or tunnel takes
  openings in its side with a `sill`; a plate lies across a climbing path or tunnel. Refused inside a sectioned
  tunnel: platforms, lifts, movers, wall switches.
- **Uneven floors and roofs.** `floor_points` (`[x, y, height]`, flat triangles between), `floor_plane`,
  `floor_lines`, the same three for ceilings, `steep_floor`; an opening needs a level sill. `levels[].bank` (sloping
  sides of a sunken or raised floor). `platforms[].top_slope` and `top_heights` (wedges, buttresses, sloping tops).
  `flights[].from_height` and `open_below`.
- **Openings.** A gable, arch or window may rise into the upright end of a dome or vault and through nested rings;
  two openings between the same two rooms, one above the other, may touch and form one mouth (wide below, narrower
  above); a ridge-to-ridge opening with `shoulders`.
- **Objects and events.** `cast` now writes level and mastery in the right order; every preset moves the doors of
  its `opens`/`closes`/`toggles` lists and a switch preset may have a door as its source; a step event may have a
  lift or mover as its source; switches and exits may be placed by `at: [x, y]` (nearest wall) and may be as wide
  as their wall; `floor_height` names the floor an object's height counts from; `random_items: 0` on a chest;
  `floors[].kind: water`; every platform form in a sunken level now stands on the sunken floor (the build warns
  where that moved one); a level-sliding mover that does not stretch carries the party.
- **Checks are stricter.** `validate` refuses a face that is not flat (naming the room), a chest standing partly
  outside its room (a sized chest's width runs ALONG its `facing`), and more; a refused object no longer drags
  follow-on messages after it.
- **Measuring.** `oymap compare` now keeps its points clear of floor edges and seams and leaves out points inside
  shut blocks; beside `report.json` it writes `points.json` with every differing point by sector, worst first: work
  from that. `oymap solve` says what stops the walk (`stopped at`) and what a branch waits for (`waiting`);
  `oymap export` takes `--mount` or a project folder; `oymap assets <name>` gives `width` and `height`; every reading
  command takes a map by path. Scores are the corrected measure's and start from the table in S3.md.

## Rules that bind (with the procedure's)

- The project files are the source. Round one's `gen/` scripts are not run. A helper that edits many rooms at once
  is allowed if every number it writes is measured from the original and you check its whole diff; keep it in your
  scratch folder and say in NOTES.md what was scripted.
- **A wrong shape that measures better is forbidden.** Every change makes the rebuild more like the original as
  measured from the original's export, not merely higher in score. If the honest shape scores lower, keep it and
  say so. Uneven floors and roofs: a height where the surface changes slope, not every vertex of the original
  (the procedure gives the budget); name the rooms whose points you took one for one.
- Work only in `devdocs/map_studio/briefs/<key>/L4/` and `output/studio_cal/<key>/`. Copy the project as it stands
  to `output/studio_cal/<key>/r4_backup/` before your first edit. Do not build the studio or the game: use
  `openyamm-studio/build/oymap` and `build/game/openyamm` as they are (another session of the user's rebuilds the
  game now and then: if a run fails because the binary is being written, wait a minute and run again). No git
  command that changes anything. `rm` only with a literal path, after `ls`, as its own command (a hook blocks
  variables and wildcards). `/tmp` is not durable.
- Build with `--out output/studio_cal/<key>/build`. Run `oymap fmt` before every check.
- Game runs: headless scenarios as the procedure says; desktop runs (`ingame_compare.py`, always with
  `--root output/studio_cal/<key>/root`) with `SDL_AUDIODRIVER=dummy` in front. Wait on exact PIDs, never on
  `pgrep -f <text>`.

## Order of work

Measure where it stands (`oymap compare <map> --world <world> --with devdocs/map_studio/briefs/<key>/L4 --assets
assets_dev --out output/studio_cal/<key>/compare_r4_start`), read `points.json`, then your map's own targets in
their order, then what `points.json` still names. Re-measure after each group of changes. Keep every reachable room
reached and `oymap solve` in the original's order; keep the playtest (`playtest.yml`) passing and extend it over
what you add; take same-camera game pairs at the places you changed and look at them yourself.

Stop when a further pass changes little or what is left needs words that do not exist. Then add "Round four" to
NOTES.md: scores at start and end (shape, textures), rooms, rooms reached, solve waves, playtest steps and result,
what changed, which new features worked and which were refused (exact message, a small repro project under
`output/studio_cal/<key>/repro/<name>/`: build repros with `--out` into a scratch folder so no `ids.lock.yml` is
written into the repro), gaps still open most harmful first (where, and the field that would say it), tool defects
with the command that shows them.

## Your final message

It is read by the lead session, not by a person. Give: the scores (start, end; shape; textures); the playtest
result; the three changes that mattered most; every refused feature with its repro path; the gaps still open in
order; any place where score and the original's true shape pulled apart and what you did. Plain facts, no padding.
