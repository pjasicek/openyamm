# Xeen map generators

The scripts that write the Map Studio projects of the World of Xeen maps (`devdocs/xeen/briefs/<map>/L1`–`L4`). Each
map's project files are the output of its generator here: change the generator and regenerate, never the written
files (the exceptions, maps whose project files are the source, are listed below). Moved here from the git-ignored
`output/studio_cal/<map>/tools/` on 2026-11-22; the old folders are symlinks to these, so older commands in notes and
lane files still work.

## Layout

```
level_generation/projects/xeen/
  regen.py            one command to regenerate (and check) any map's project files
  <map>/              one folder per map: the generator (gen.py and its helpers), its playtest writers,
                      its drivers (cycle.sh, v.sh, vw.sh, b.sh, go.sh), small hand data (x1's house_doors.yml,
                      pois.yml) and, for the outdoor maps, bake_profile.json (the lighting bake profile)
  dd11/               shared by dd11a, dd11b and dd11c (lib.py); dd10a/mine.py is shared by dd10a-c the same way
  common/
    beds/             beds.py and the outdoor ambient sound beds (<map>.yml) the outdoor generators merge into
                      their sketches (A5's, A6's and AU's lists, all in one place)
    planes/           pieces.py: the plane pieces shared by P1-P4 (and sheet.py, tour_pieces.py)
    hostility/        gen_hostility_tests.py: the first hostility pass (2026-11-16); the outdoor
                      gen_hostility_<map>.py scripts exec it
    entrance.py       the standard entrance window rows of the outdoor maps' dungeon doors (A5 s29, F16/D-90)
    gen_daily.py      P1's playtest_daily.yml (daily sources)
    d85.py            the D-85/D-87 distance check of A6's outdoor maps (X2's own is x2/check_d85.py)
    install/          the lanes' install scripts (see "Install and bake")
    bake/             the lanes' lighting bake scripts
    run/              game_slot.sh (two games at a time, each through tools/heavy.sh 6) and xfour.sh (A7's
                      playtest runner)
    dressing/         A7's dressing checks (formats/DRESSING.md): check_dressing.py <L4> <built map json>,
                      measure.py, suggest_moves.py and the line fixers used on XD-01 to XD-05 and D7
  xd01/ ... xd05/     no generator: their review scripts, and history/ (below)
```

Each map folder also holds the map's review and run scripts, moved from `output/studio_cal/<map>/` on 2026-11-22
(`four.sh` playtests N times, `look.sh` / `tour.sh` / `shots.sh` / `shoot.sh` screenshot tours, `play.sh` a play copy,
`stage.sh` / `stage_install.sh` a staged install, `walk.sh` ...; P5's, X9's and XD-17's playtest runner is
`run_tests.sh`, the old `run.sh`). Every game they start goes through `tools/heavy.sh 6` (or `common/run/game_slot.sh`,
which does), with `SDL_AUDIODRIVER=dummy` and `OPENYAMM_START_MINIMIZED=1` exported at the top; windowed runs use
`tools/run_game.sh --isolated`; waits are on exact PIDs. Their logs, user-data folders and shots stay in
`output/studio_cal/<map>/` (`run/`, `shots/`, ...). Many take the asset root in `ASSETS` and a test list in `TESTS`;
read the header of each before running it.

**history/** (XD-01 to XD-05 only): the first-pass generators and the one-off scripted edits that made these maps
(`pass2/edit_p2*.py`, `pass3/edit_p3.py`, `a7_move.py`, `a7_dressing/batch*.py`, ...). They are a record: the project
files in `devdocs/xeen/briefs/<map>/` are the source, and these scripts must not be rerun (their paths into
`output/studio_cal/` are the old ones).

Work output never goes here. Builds, scratch roots, shots, logs and bakes stay in the git-ignored
`output/studio_cal/<map>/` (`build/` or `build_w/`, `root/`, `run/`, `shots/`, ...): the scripts find the repository
root from their own location (`_REPO_ROOT`, or `$(dirname "$(readlink -f "$0")")/../../../..` in the drivers) and
write there as before. Keep folder names out of `level_generation/.gitignore`'s skipped list (`work/`, `review/`,
`renders/`, `before*/`, `maps/` ...): a script in such a folder is not tracked. After adding files, run
`python3 level_generation/update_gitignore.py` (nothing here may exceed 256 KB).

Generated text still names the old paths: notes inside the written project files say "Written by
output/studio_cal/<map>/tools/gen.py" and the playtest headers likewise. Those strings were left as they were so the
regenerated files stay byte-identical; the old paths are symlinks to these folders. Change them together with a
deliberate change of the project files.

## Regenerating

```
python3 level_generation/projects/xeen/regen.py <map> [<map> ...]   # write the project files (gen + oymap fmt)
python3 level_generation/projects/xeen/regen.py --check <map>       # write, list what differs, put the files back
python3 level_generation/projects/xeen/regen.py --check all
python3 level_generation/projects/xeen/regen.py --build <map>       # P1-P5, X8, X9, D7: also build L4 and run the
                                                                     # playtest writer that reads the build
```

`regen.py` runs each generator step through `tools/heavy.sh 8`, then `openyamm-studio/build-xeen/oymap fmt` on the
levels the generator writes, then the map's playtest writers that need no build. Run `--check` before you change a
generator: it shows whether the committed files still match the generator (someone may have edited them since); a
hand edit would be lost by a rerun. The map's own driver does the whole cycle (generate, fmt, validate, build into
`output/studio_cal/<map>/build`, install into its scratch root, audit): `level_generation/projects/xeen/<map>/cycle.sh`
for most dungeons, `v.sh` / `vw.sh` (then `b.sh`) for the outdoor maps, planes and sky maps, `go.sh` for XD-10 and
XD-11. Per-map locks: `flock output/xeen_locks/xeen_<map>.lock <command>` around edit, build, install and bake.

## Maps

"Reproduces" means: `regen.py --check <map>` on 2026-11-22 wrote every project file byte for byte as committed. The
playtest writers that read a build (`gen_walk.py`, `gen_daily.py` of X4, `gen_hostility_d5.py`) are not part of
`regen.py`; see the notes below the table.

| Map | Name | Entry point | Reproduces |
|---|---|---|---|
| d1 | Castleview Vale | `d1/gen.py`, `gen_hostility_d1.py` | yes |
| d2 | Sprite Forest and Ogre Pass | `d2/gen.py`, `gen_hostility_d2.py` | yes |
| d3 | Sandcaster and the Aging Forest | `d3/gen.py`, `gen_hostility_d3.py` | yes (L1-L4); `gen_fall.py` no, see below |
| d4 | Lakeside and Blackfang | `d4/gen.py`, `gen_hostility_d4.py` | yes |
| d5 | Desert of Doom | `d5/gen.py` | yes |
| d6 | The Forbidden Zone | `d6/gen.py`, `gen_hostility_d6.py` | yes |
| d7 | The Skyroads | `d7/gen.py`, `gen_plan.py`, `gen_objects.py`, `gen_playtests.py` (build) | yes |
| dd01 | Castleview Sewer | `dd01/gen.py` (`geo.py`, `dress.py`) | yes |
| dd02 | Ellinger's Tower | `dd02/gen.py` | yes |
| dd03 | Castle Kalindra | `dd03/gen.py` | yes |
| dd04 | The Gremlin Court | `dd04/gen.py` | yes |
| dd05 | Western Tower of Mok | `dd05/gen.py` | yes |
| dd06 | Southern Tower | `dd06/gen.py` | yes |
| dd07 | Eastern Tower | `dd07/gen.py`, `gen_tests.py` | yes |
| dd08 | Northern Tower | `dd08/gen.py` (`geo.py`, `dress.py`) | yes |
| dd09 | Temple of Bark | `dd09/gen.py` (`geo.py`, `dress.py`) | yes |
| dd10a | Gemstone Mines, west pocket | `dd10a/gen.py` (`mine.py`) | yes |
| dd10b | Gemstone Mines, east pocket | `dd10b/gen.py` (`../dd10a/mine.py`) | yes |
| dd10c | Gemstone Mines, north pocket | `dd10c/gen.py` (`../dd10a/mine.py`) | yes |
| dd11a | Troll Holes, first pocket | `dd11a/gen.py` (`../dd11/lib.py`) | yes |
| dd11b | Troll Holes, second pocket | `dd11b/gen.py` (`../dd11/lib.py`) | yes |
| dd11c | Troll Holes, third pocket | `dd11c/gen.py` (`../dd11/lib.py`) | yes |
| dd12 | Dungeon of Lost Souls | `dd12/gen.py` | yes (since 2026-11-24: the two hand-moved chests are in `gen.py`) |
| dd13 | Ogre Forts | `dd13/gen.py` | yes |
| dd14 | Castle Blackfang | `dd14/gen.py` (`geo.py`, `dress.py`) | yes |
| dd15 | Great Pyramid | `dd15/gen.py` (`geo.py`, `dress.py`) | yes |
| dd16 | Corak's Pod | `dd16/gen.py` | yes |
| dd17 | Castle Alamar | `dd17/gen.py` (`geo.py`, `dress.py`), `tests.py` | yes |
| dd18 | Sandcaster Sewer | `dd18/gen.py` (`geo.py`, `dress.py`) | yes |
| dd19 | Wizard Quarter | `dd19/gen.py` (`geo.py`, `dress.py`) | yes |
| dd20 | Lakeside Coven and Sewer | `dd20/gen.py` (`geo.py`, `dress.py`) | yes |
| dd21 | Necropolis Sewer | `dd21/gen.py` (`geo.py`, `dress.py`) | yes |
| dd22 | Sheltem's Pod | `dd22/gen.py` (`geo.py`, `dress.py`) | yes |
| dd23 | Gargoyle Lair | `dd23/gen.py` | yes |
| dd24 | Giants' Hall | `dd24/gen.py` | yes |
| dd25 | Bosco's Hall | `dd25/gen.py` (`geo.py`, `dress.py`) | yes |
| dd26 | Olympus Sewer | `dd26/gen.py` (`geo.py`, `dress.py`) | yes |
| fd01 | Alamar Depths | `fd01/gen.py` (`geo.py`, `dress.py`), `tests.py` | yes |
| fd02 | Southern Sphinx | `fd02/gen.py`, `gen_tests.py` | yes |
| fd03 | Darkstone Tower | `fd03/gen.py`, `gen_tests.py` | yes |
| fd04 | Dragon Tower and the Dungeon of Death | `fd04/gen.py`, `gen_tests.py` | yes |
| p1 | Plane of Fire of Xeen | `p1/gen.py`, `gen_playtests.py` (build), `../common/gen_daily.py p1` | yes |
| p2 | Plane of Air of Xeen | `p2/gen.py`, `gen_playtests.py` (build) | yes |
| p3 | Plane of Earth of Xeen | `p3/gen.py`, `gen_playtests.py` (build) | yes |
| p4 | Plane of Water of Xeen | `p4/gen.py`, `gen_playtests.py` (build) | yes |
| p5 | Clouds of the Ancients | `p5/gen.py`, `gen_plan.py`, `gen_objects.py`, `gen_playtests.py` (build) | yes |
| x1 | Vertigo Meadows | `x1/gen.py <L4 folder>` (`town.py`, `dress.py`; writes `house_doors.yml`, `pois.yml` here) | yes |
| x2 | Rivercity and Lake Darzog | `x2/gen.py`, `gen_hostility_x2.py` | yes |
| x3 | Lifeforce Lagoon | `x3/gen_l1.py`, `gen.py`, `gen_hostility_x3.py` | yes |
| x4 | Burlock Savannah | `x4/gen.py`, `gen_hostility_x4.py` | yes |
| x5 | Winterkill Tundra | `x5/gen.py`, `gen_hostility_x5.py` | yes |
| x6 | Desert of the Sphinx | `x6/gen.py`, `gen_hostility_x6.py` | yes |
| x7 | Mount Firestone | `x7/gen.py`, `gen_hostility_x7.py` | yes |
| x8 | Cloudreach | `x8/gen.py`, `gen_plan.py`, `gen_objects.py`, `gen_playtests.py` (build) | yes |
| x9 | Clouds of Xeen | `x9/gen.py`, `gen_plan.py`, `gen_objects.py`, `gen_playtests.py` (build) | yes |
| xd01 | Joe's Warehouse | none: the L4 files are the source | n/a |
| xd02 | Red Dwarf Mines | none: the L4 files are the source | n/a |
| xd03 | Deep Mine | none: the L4 files are the source | n/a |
| xd04 | Witch Tower | none: the L4 files are the source | n/a |
| xd05 | Orc Caves | none: the L4 files are the source (`gen.py` refuses: "gen.py is stale: edit L4 directly") | n/a |
| xd06 | Temple of Yak | `xd06/gen.py`, `gen_plan.py` | yes (L4; L1-L3 kept, see below) |
| xd07 | Castle Burlock | `xd07/gen.py` | yes |
| xd08 | Tomb of a Thousand Terrors | `xd08/gen.py` | yes |
| xd09 | Golem Dungeon | `xd09/gen.py` | yes (L4; L1-L3 kept, see below) |
| xd10 | Cave of Illusion | `xd10/gen.py L4` (`geo.py`, `dress.py`) | yes |
| xd11 | Tower of High Magic | `xd11/gen.py L4` (`geo.py`, `dress.py`) | yes |
| xd12 | Darzog's Tower | `xd12/emit.py L4` (`plan.py L1`/`L2`, `emit.py L3`; `shell.py`, `geo.py`, `dress.py`) | yes |
| xd13 | Newcastle Keep | `xd13/gen.py` | yes |
| xd14 | Castle Basenji | `xd14/gen.py` | yes |
| xd15 | The Sphinx | `xd15/gen.py L4`, `gen_tests.py` | **no**: one chest moved by hand in L4 objects.yml, see below |
| xd16 | Volcano Cave | `xd16/gen.py L4`, `gen_tests.py` | yes |
| xd17 | Shangri-La | `xd17/gen.py`, `gen_playtests.py` | yes |
| xd18 | Dragon Cave | `xd18/gen.py`, `gen_tests.py` | yes |
| xd19 | Castle Xeen | `xd19/gen.py`, `gen_tests.py` | yes |
| xd20 | The Warzone | none: hand-written L4 (an arena of three rooms, no L1-L3) | n/a |
| xd21 | Robbers' Den | `xd21/gen.py`, `plan.py` | yes (L4; L1-L3 kept, see below) |
| xd22 | Ninja Pagoda | `xd22/gen.py` | yes |
| xd23 | Troll Warren | `xd23/gen.py` | yes |
| xd24 | Nightshadow Crypt | `xd24/gen.py` | yes |
| xd25 | Asp Undercroft | `xd25/gen.py` | yes |
| xd26 | Gargoyle Eyrie | `xd26/gen.py` | yes |
| xd27 | Ogre Lair | `xd27/make_l3.py`, `gen.py --l3`, `gen.py` | yes |

The command for every map is `python3 level_generation/projects/xeen/regen.py <map>` (`--build` for the maps marked
"build"). The playtests of the dungeons are hand-written unless the table names a writer.

### Known differences

- **XD-15**: `chest:vault` at (384, 6104) against the generator's (0, 6040).
  The chests were moved in the project files after the generator's last run (the chest and props fixes of the
  2026-11-21 feedback round). Before regenerating either map, carry the positions into `gen.py`, or the rerun moves
  the chests back.
- **XD-06, XD-09, XD-21**: the generators (`gen_plan.py`, `gen.py`, `plan.py`) still write L1-L3 too, and those no
  longer match the committed, approved levels (L1-L3 stay as approved since D-58). `regen.py` puts L1-L3 back after
  the run; the L4 files reproduce.
- **XD-01 to XD-05, XD-20**: no generator. XD-01 to XD-04 were made by first-pass generators and then scripted one-off
  edits (`edit_p*.py`, `fix*_p*.py`, kept as a record in `xd0N/history/`): their notes say the files are the
  source and the generators must not be rerun. Edit their project files directly (or with `oymap`).
- **`common/hostility/gen_hostility_tests.py`** (keys x1, x2, xd01-xd06, xd12, xd21, xd27) no longer writes what is
  committed: those `playtest_hostility.yml` files were rewritten for the Xeen world rows afterwards (they read
  `world: xeen` and the Xeen monster ids; the pass wrote MM7 stand-ins). Keep it for the `gen_hostility_<map>.py`
  scripts that exec it; do not run it for those keys. X1's own `gen_hostility_x1.py` is superseded the same way.
- **D3 `gen_fall.py`** writes `playtest_d7_fall.yml` from the installed world's arrival points, which have moved since
  (D7's fall spots); the committed file holds the older points.
- **Build-dependent playtest writers.** The outdoor `gen_walk.py` (`playtest.yml` of D1-D6, X1-X7), X4's
  `gen_daily.py` and D5's `gen_hostility_d5.py` take `<L4 folder> <build folder>` (see each Usage line) and read a
  fresh build. With the scratch builds of 2026-11-22 they reproduced D1, D2, D4 and D6; X5's differs only in the
  line wrapping of one Lua string; the others need a rebuild first (`v.sh` / `vw.sh`). `common/gen_daily.py` knows
  only P1 now.

## A fix that applies to every map

The user's rule (FEEDBACK_FIX_RULES.md, memory "studio feedback generalises"): a fault found on one map is fixed
at its source for every map of its kind, with a check that keeps it fixed, never patched in the one map's files.

1. Find the source: the Map Studio (`openyamm-studio/`, A1 builds it), a shared Xeen tool (`tools/xeen/`, e.g.
   `kit_pieces.py`, `villagers.py`, `cave_shape.py`), a shared library here (`common/`, `dd11/lib.py`,
   `dd10a/mine.py`), or the same idiom repeated in each map's generator (the outdoor `kit.py` copies, the
   `geo.py`/`dress.py` dungeons).
2. Change it there, then regenerate every map that uses it: `regen.py --check all` first (to see which maps still
   reproduce), then `regen.py <maps>`, and review `git diff devdocs/xeen/briefs/` (only your change should appear).
3. Add the check: an `oymap audit` rule (A1), a check in `tools/xeen/` (check_exits, check_drops, door_check,
   wall_check, check_open_sky ...), or a refusal in the generator.
4. Rebuild, install and bake the changed maps (lanes/README.md "Memory": every build through `tools/heavy.sh 8`,
   bakes under `flock output/xeen_locks/bake.lock` through `tools/heavy.sh 16`).

## Checks after regenerating

- `oymap fmt --check` and `oymap validate <L4> --assets assets_dev` (regen.py formats already).
- Build and audit: `tools/heavy.sh 8 openyamm-studio/build-xeen/oymap build <L4> --assets assets_dev --out
  output/studio_cal/<map>/build`, then `oymap audit <built or installed map> --world xeen --assets <root> --reach
  --solve` (the map's `cycle.sh` / `v.sh` does all of this). Every audit error fixed; warnings fixed or listed under
  "Dressing exceptions" in the map's NOTES.md.
- The Xeen checks of lanes/README.md: `tools/xeen/check_exits.py`, `check_drops.py <map.blv>`, `door_check.py`,
  `wall_check.py <stem>` and `house_signs.py` (walled outdoor places), `check_open_sky.py <key>` (indoor sky faces),
  the D-85/D-87 distance check of outdoor maps (`x2/check_d85.py <scene> [radius]`, `common/d85.py`), and after an
  install `tools/xeen/key_npcs.py --write` and `check_actor_heights.py`.
- Dressing (indoor maps): `common/dressing/check_dressing.py <L4> <built map json>` (formats/DRESSING.md).
- Indoor maps after a rebuild: `python3 tools/maw/xeen_pack_reserve.py <stem>` and `tools/maw/xeen_balance.py --check`.
- The map's playtests (`devdocs/xeen/briefs/<map>/L4/playtest*.yml`) as headless scenarios through
  `tools/heavy.sh 6` (the map's `four.sh` here runs them), and `tools/lighting/stale_bakes.py`
  after an install.

## Install and bake

Install a map only with its bake, straight after (assets_dev must never hold a map newer than its lighting), under the
map's lock (`flock output/xeen_locks/xeen_<map>.lock`). The scripts below are the lanes' own, moved here on 2026-11-22;
every heavy step runs through `tools/heavy.sh` (oymap 8, terrain tool 8, Blender bake 16, game 6). Work output (stages,
bakes, logs) stays in the lane's or the map's folder under `output/studio_cal/`.

Outdoor maps (D1-D6, X1-X7; profile `level_generation/projects/xeen/<map>/bake_profile.json`), after the map's
`v.sh` / `vw.sh` built it:

```
level_generation/projects/xeen/common/install/a6_install_baked.sh xeen_<map> devdocs/xeen/briefs/<map>/L4 \
    output/studio_cal/<map>/build level_generation/projects/xeen/<map>/bake_profile.json
```

`a6_install_baked.sh` (A6's maps D1, D2, D4-D6, X5) makes a hard-link stage of assets_dev with the world's tables
copied, installs into it (`oymap install`), bakes from it under `output/xeen_locks/bake.lock`, copies the map and its
bake into assets_dev by new file and rename, runs `install/terrain_swap.sh` (terrain weights and liquid edges in a
private root, swapped in file by file) and `stale_bakes.py`, and removes the stage. `a5_install_baked.sh` is A5's
version for D3, X1-X4, X6, X7 (their build folder is `build_w` for D3, X3, X4, X6, X7; its own lane lock `output/studio_cal/a5/locks/blender.lock`, an optional
`--sources DIR`; it leaves the stage for removal by its printed literal path). `a6_install_baked.sh` takes the
program's bake lock itself around its Blender run: never wrap it in `flock output/xeen_locks/bake.lock` (that deadlocks
every bake in the program, 2026-11-23). `a5_install_baked.sh` takes only its lane lock: wrap it in the bake lock.

Dungeons (indoor maps):

```
INSTALL=1 level_generation/projects/xeen/common/install/a8_rebuild.sh <map>     # build, stage, install the map's files
flock output/xeen_locks/bake.lock level_generation/projects/xeen/common/bake/a8_bake.sh <map> assets_dev
```

`a8_rebuild.sh` (fmt, validate, build into `output/studio_cal/<map>/b_<time>`, `oymap install --mount` into a stage,
and with `INSTALL=1` `install/install_stage.py` copies only the map's own files into assets_dev); `a8_bake.sh` bakes
from the given root with the map's profile `tools/lighting/baked_indoors/profiles/xeen_<map>.yml` into
`output/studio_cal/<map>/a8_bake/bake` and installs the bake beside the map. A7's equivalents: `install/a7_xcycle.sh`
(build and install into A7's scratch root, audit), `install/a7_install_baked.sh <root> <map>...` (bake from that root
with `bake/a7_bake_map.sh`, then the map and its bake into assets_dev), `install/install_bake.py <map>` (an A7 bake
into assets_dev). `bake/a8_lights_post.sh <map>` bakes from assets_dev and runs the map's `four.sh`. The open-air
maps (P1-P5, X8, X9, D7, XD-17) install with their `stage_install.sh` / `b.sh`.

After every install: `tools/xeen/key_npcs.py --write`, `tools/xeen/check_actor_heights.py`,
`tools/lighting/stale_bakes.py --check` (0), and for indoor maps `tools/maw/xeen_pack_reserve.py <stem>` and
`tools/maw/xeen_balance.py --check`.

Dry-checked on 2026-11-22: `bash -n` on every script here, `a8_rebuild.sh dd06` with `INSTALL=0` (built and staged,
nothing installed) and `run/game_slot.sh`; no bake or install was run.

## Still outside the tracked tree

The scratch roots (`output/studio_cal/<map>/root`, `output/studio_play/xeen_root`), builds, stages and bakes; the
lanes' session queues and one-off chains (`a7/s18/install_queue.sh`, `a7/s26/bakew.sh`, `a8_s8/queue_polish1.sh`,
`a5/mp24_q.sh`, `a7/s*_chain.sh` ...), which name the maps and states of their session. None of them is needed to
regenerate, install or bake a map.
