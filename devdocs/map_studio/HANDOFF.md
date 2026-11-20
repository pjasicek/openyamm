# Map Studio handoff

Kept current by the lead session; the user asked on 2026-11-13 for an update every 30 minutes while work runs. The
block "Status" below is rewritten each time; the rest changes when a fact changes.

Read this first, then `S3.md` from "Round three merged" to "WebAssembly" (the record of what was built and
measured, round by round), `REBUILD_PROCEDURE.md` (dungeons), `OUTDOOR_REBUILD_PROCEDURE.md` (outdoor maps),
`rounds/ROUND_FOUR.md` (how a round's common brief looks) and `openyamm-studio/README.md`. Older: the first part of
`S3.md`, `S2.md`, `S1.md`, `S0.md`, `PLAN.md`.

## Status (2026-11-15, 19:21)

**A new lead session takes over from `HANDOFF_LEAD.md`** (written 19:21): where the studio stands (S0-S6 done apart from
what waits on the user; S7 in flight), the user's decisions, how to merge and check, the rules, and the open work.
The older blocks that stood here (S3 and S4 history) are summarised there; `S3.md` and `S5.md` are the detailed
records.

## What the work is

Map Studio (`openyamm-studio/`, untracked, its own build) builds MM6-8 indoor maps (BLV, scene, Lua) and classic
ODM outdoor maps from YAML projects. The user reviews **results only**, on `output/studio_review/index.html`
(written by `python3 openyamm-studio/calibration/review_page.py`, which re-measures every rebuild when run), and
asked for a **self-correcting loop**: rebuild shipped maps as projects, measure them against the originals by tool
(`oymap compare`, indoor and outdoor), build what the vocabulary lacks, repeat, without the user pointing at
differences. On 2026-11-12 the user added: do the outdoor maps as well; and agreed to build one new dungeon from a
written brief with no original (XD-01).

## Where this sits in the plan

`PLAN.md` section 12 has the milestones with what each delivers and how it is accepted.

| Milestone | State | Record |
|---|---|---|
| S0 skeleton, briefs, vertical slice | done | `S0.md` |
| S1 read side and metrics | done; its game-side cuts were committed on 2026-11-13 (`dfd7a236ac`) | `S1.md` |
| S2 operations, host, agent interface | done except map reload in the running game, HTTP/jobs | `S2.md` |
| S3 indoor authoring | **accepted 2026-11-13 (20:30)** pending the user's word: every map within the bands and walked by the user (the Forge, Warlord's Fortress, Control Center, the Temple of the Moon, Darkmoor in part, the Hive on its fixes, the Mad Necromancer's Lab and Goblinwatch held out, XD-01 to XD-05); set-piece import and the Python port dropped | `S3.md` |
| S4 outdoor authoring | **in work.** A sketch builds into a classic ODM with land, ground and shore tiles, roads, buildings of several parts, walls, bridges, wells, chests, signs, people, monsters, scatter, weather and travel off its edges; an outdoor `oymap compare`. Acceptance not met: Ravenshore and Harmondale are being calibrated; New Sorpigal, Shadowspire and Vertigo Meadows are not started | `S3.md` from "Second code batch merged" |
| S5 browser editor, S6 MM9 profiles, S7 consolidation | not started | `PLAN.md` |

The lead's own estimate of the dungeon work, given to the user on 2026-11-12 (a judgement, not a measurement): shape
and textures of shipped dungeons about 90 % there, behaviour 70 %, contents 40 %, new dungeons from a description
25 %, the rest of the milestone 20 %; about two thirds overall. After XD-01 (2026-11-13) the lead put "new dungeons
from a description" at about 40 %: a brief becomes a playable dungeon in the right order with one strong area,
but not every room is worth looking at and several things a designer reaches for are missing.

## State of the maps

Dungeons: `devdocs/map_studio/briefs/<key>/L4/`, each with `NOTES.md` (a section per round) and `playtest.yml`;
scratch, pictures and repro projects in `output/studio_cal/<key>/`. Scores are the lead's measurement of 2026-11-13, 09:18 (equal to the
round-five reports), and the later rounds' reports (the Forge's finishing round, the Temple's round six, the Fortress); the measure is the corrected one (S3.md, "Round three merged", links it to
earlier figures). All validate, build and pass their playtests four of four by their reports.

| Map | Key | Score | Rounds |
|---|---|---|---|
| Gharik's Forge (MM6 6d18.blv) | `mm6_6d18` | 99.7 % | five and a finishing round; played by the user |
| Control Center (MM6 sci-fi.blv) | `mm6_scifi` | 99.4 % | six and the ninth merge's lines; the user (16:39): "good" |
| Castle Darkmoor (MM6 cd2.blv) | `mm6_cd2` | 99.2 % | six; 267 rooms |
| The Hive (MM6 hive.blv) | `mm6_hive` | 97.7 % | six; 100 rooms |
| The Lincoln (MM7 7d23.blv) | `mm7_7d23` | 97.4 % | five and the ninth merge's lines; playtest ten of ten |
| Goblinwatch (MM6 6d01.blv), held out | `mm6_6d01` | 99.2 % | one |
| The Mad Necromancer's Lab (MM8 d20.blv), held out | `mm8_d20` | 99.7 % | one |
| Abandoned Temple (MM8 d05.blv) | `mm8_d05` | 97.2 % | seven; the user's walk; arrival view fixed |
| Temple of the Moon (MM7 7d06.blv) | `mm7_7d06` | 97.5 % | seven |
| Warlord's Fortress (MM6 6d16.blv) | `mm6_6d16` | 99.7 % | one (L3 to L4) and the ninth merge's lines; the user: "plays exactly the same" |

Outdoor: the same folders, by OUTDOOR_REBUILD_PROCEDURE.md. Their first sketches were written from the originals
by scripts (`output/studio_s4c/gen/`; not run again) and then worked over by one rebuild round each; scores are
the lead's measurement of 2026-11-13, 01:35, with the stricter decorations part. They show what the builder can build from a careful description of
a known map, not yet a map from a written brief.

| Map | Key | Score | State |
|---|---|---|---|
| New Sorpigal (MM6 oute3.odm), held out | `mm6_oute3` | 93.53 % | two; the user's 21 places |
| Shadowspire (MM8 out06.odm), held out | `mm8_out06` | 92.12 % | three; the dragon cave and the Lab |
| Ravenshore (MM8 out02.odm) | `mm8_out02` | 92.20 % | five rebuild rounds |
| Erathia (MM7 7out03.odm), fresh | `mm7_7out03` | 91.4 % (89.5 without node heights) | two; O-H words and the building shots |
| Castle Ironfist (MM6 outd3.odm), fresh | `mm6_outd3` | 93.91 % (94.16 without the rim) | three; the castle roof reached on foot |
| Harmondale (MM7 7out02.odm) | `mm7_7out02` | 90.23 % (87.22 without the rim) | seven rebuild rounds; inside the band |

New: XD-01 Joe's Warehouse, `devdocs/xeen/briefs/xd01/L4/`: built from its brief on 2026-11-13 and given a second
pass (26 rooms, playtest 110 steps), in MM7's world as a stand-in. XD-02 the Red Dwarf Mines,
`devdocs/xeen/briefs/xd02/L4/`: built from its brief the same day (43 rooms, playtest 171 steps). XD-03 the Deep Mine,
`devdocs/xeen/briefs/xd03/L4/`: built from its brief the same day (24 rooms, walks of 175 and 46 steps; the first
under the texture rule). XD-04 and XD-05 have L1 to L3 only. XD-01 and XD-02 are in a texture pass (10:14, 10:25).
Warlord's Fortress (`briefs/mm6_6d16`) reached L4 on 2026-11-13 (99.7 %), in the maps table above.

The review page's Temple pictures come from a copy: before regenerating, copy `briefs/mm7_7d06/L4/*.yml` and
`diagram.txt` into `output/studio_temple/project`, build it, and run `python3
openyamm-studio/calibration/ingame_compare.py output/studio_temple/project mm7 7d06.blv
output/studio_temple/shots.yml output/studio_temple/compare --root output/studio_temple/root`; then update the
"State of these pictures" note in `review_page.py`.

## Rules that bind (the user's)

- No `git add`, `commit`, `stash`, `restore --staged`, `reset` unless asked. The studio and its docs are
  uncommitted on purpose (below).
- Never copy code from OpenEnroth or mm_mapview2. Never edit generated Lua or MM9 converter output. `assets_dev`
  files are hard links in every `cp -al` root: never edit in place. `/tmp` is not durable.
- `rm` only with literal paths, after `ls`, in its own command (a hook blocks variables and wildcards).
- No game build while an MM9 `convert.py` runs; game builds go through the lane (`flock -x
  level_generation/projects/mm9r_common/locks/cmake_build.lock cmake --build build --target openyamm -j25`); no
  Vulkan builds. Game runs minimised through `tools/run_game.sh`, `SDL_AUDIODRIVER=dummy` in front; review shots
  with the HUD off.
- Manual fix-ups live in the project, never in built maps. Outdoor is classic ODM.
- **A wrong shape that measures better is forbidden.** Check every agent report for it. Cases so far: a roof bent
  to a wrong pitch (round two, set back); slabs widened by 2 to 4 units to catch the measure's edge points (in the
  Forge since round one, found and undone by its round-three agent; the measure was then corrected).
- A fix for something the user saw is proven in the game on a part that shows the fault, before and after.

## The user's decisions

- **Models (2026-11-12; changed 2026-11-13):** on 2026-11-12 lead and code agents on the strongest model (Fable),
  effort high, rebuild agents on Opus. On 2026-11-13 the Fable limit was reached at about 02:00 and the user set the
  session to Opus 5.5; until the user says otherwise everything runs on Opus. Original note: rebuild agents on Opus
  (`model: opus` on the Agent call; agents inherit the lead's model unless told). A rebuild or code agent uses 350
  to 790 thousand tokens.
- **Scripts may write project files (2026-11-12).** Kept as a record, never re-run once a project has hand edits;
  both procedures say how. Uneven floors and roofs are given by points where the surface changes slope, within a
  budget; rooms that took the original's points one for one are named in NOTES.md.
- **Game-side changes are allowed when no existing map changes (2026-11-12).** Done so far: the `water` surface
  flag in the indoor compiler; a level-sliding door carries the party when its scene `mover` block has `carry:
  true`. Anything else outside `openyamm-studio/` is asked first.
- **The moving-texture rule stays in the studio (2026-11-12),** not in the game's indoor compiler: the user fears
  regressions. Not to be moved unless an MM9 conversion shows a sliding texture. (What it is: S3.md, "Textures on
  moving parts"; `anchorMovingFaceTextures` in `core/IndoorBuild.cpp`.)
- **Outdoor as well (2026-11-12, 20:45),** and tunnels need their cross-section (built: `section` on path rooms).
- **XD-01 from its brief (2026-11-12, 23:40):** agreed, "if you feel it is best".
- **Committed (2026-11-13):** the release session openyamm-f4 committed this work's game-side changes in
  `dfd7a236ac` (the S1 and S2 cuts, `--extra-mount`, carry, water). `openyamm-studio/`, `devdocs/map_studio/`,
  `devdocs/xeen/` and `.github/workflows/studio.yml` stay untracked: whether and how the studio enters the
  repository is the user's to decide. Never done: checking the 7 failing full-suite game unit cases against a
  clean tree.
- Gharik's Forge's lava: decided by the lead on 2026-11-13 to follow the original's data (timer only); the finishing
  round found that OpenYAMM's own overlay adds the lava flag in the shipped game, so the rebuild now burns less than
  the shipped game. Asked of the user.

- **2026-11-13, about 12:15:** the Forge's lava as OpenYAMM ships it (the floors burn, and the timer stays; applied,
  playtest four of four, in the user's copy). The textures the Xeen dungeons list: generate them ("sure no
  problem"). "Within bands" is the lead's to define (below). Set-piece import and the Python port: the lead's
  recommendation, dropped (PLAN.md 2a). A git snapshot of `devdocs/map_studio` and `devdocs/xeen`: yes (`a761ce68bd`;
  project build folders ignored; `openyamm-studio/` stays out). The user plays maps to judge them: give run
  commands (`output/studio_play/PLAY.md`), not only pictures; on the fixed Forge: "this plays exactly the same as
  original one".
- **Within bands (the lead's definition, 2026-11-13).** A rebuilt dungeon is within bands when: `oymap compare` is at
  least 97 % overall; its playtest goes from the arrival to the exit and passes every run (four of four, nothing left
  to chance); every event of the original does the same or is listed as unsayable; the "what the measure does not
  see" pass is done (every interactive thing pictured beside the original's before and after use, the view from
  every raised top, no fault left that the project can say); and no fault from the user's play is open. An outdoor
  map: at least 90 % with the rim part, its walk two of two, the same pass. A new dungeon: scale inside the bands of
  MAP_CRAFT_CALIBRATION.md, its playtests every run, the texture rule met, and the user's walk. Today: the Forge
  meets them (and the user's walk); Control Center, Castle Darkmoor, Warlord's Fortress and the Hive meet the numbers
  and wait for the user's walk; the Lincoln (a chance failure), the Abandoned Temple (96.9 %, the black arrival
  view) and the Temple of the Moon (95.9 %) do not yet.

## Build and checks

```
cd openyamm-studio && ./build.sh          # native: build/oymap, build/oymap_tests   (wasm: ./build.sh wasm)
build/oymap_tests                         # 189 cases at the last merge
tests/run_shapes.sh [--shots]             # the test map: walk of 450 steps in the game, 113 tour pictures
tests/run_slice.sh ; tests/run_rewire.sh ; tests/native_vs_wasm.sh ; (cd host && node test/mcp.test.mjs [--play])
python3 calibration/review_page.py        # re-measures all maps and writes output/studio_review/index.html
```

`tests/run_shapes.sh` checks one line of `oymap solve` on the test map (`step 1: 29 sectors (63 of 71)` now): it
changes whenever rooms are added there; set it to what the merged build gives.

## Merging code agents' work

Code agents share the source tree and build only into their own trees (`build-geo`, `build-cmp`, `build-fix`,
`build-s4`; the lead's was `build-lead`; all may be removed when no agent runs). Rebuild agents use
`build/oymap` and `build/game/openyamm` as they are. So:

1. Do not rebuild `build/oymap` while rebuild agents run unless existing projects build to the same bytes.
2. When the rebuild agents have finished: keep a copy of the old `build/oymap`, `./build.sh`, unit tests, set the
   solve line, `tests/run_shapes.sh --shots`, slice, rewire.
3. Build all seven dungeon projects with the old and the new binary and compare (`.blv`, `.scene.yml`, `.lua`);
   explain every difference; play all seven playtests (several times where one loots chests: a playtest must not
   depend on what chests roll).
4. Re-measure everything with `review_page.py`; where the measure itself changed, measure the same projects with
   the old binary too and record both (S3.md has such tables).
5. Refresh the Temple's review copy, add new test-map shots to `SHOTS` in `review_page.py`, regenerate.
6. Record in S3.md; update this file.

Editing `review_page.py` by script: `PAGE` is one long string and the placeholders (`@INGAME@` and the like) occur
twice, once in `main()` and once in `PAGE`: search from the right place, and parse the result before writing (it
was duplicated twice this way).

## Other sessions

No other session works on the studio. openyamm-fe, which drew the Temple of the Moon and the Xeen briefs, no longer
exists (the user, 2026-11-12). Other sessions of the user's work in the repository (openyamm-a7 on saves,
openyamm-f4 on the 2.2 release) and rebuild `build/game/openyamm` every half hour or so: a run that hits a
half-written binary is retried after a minute; a playtest failure that smells of saves or loading is checked
against their work first.

## Open, beyond the checklist above

- Tool defects not with an agent (S3.md, "Round four", last bullet): event casts cannot be asserted in a headless
  run, in the original either (so traps are known to fire the right call, not to hurt); `oymap build --out` and
  `oymap export <project>` write `ids.lock.yml` into the folder they read.
- The measure sees shape and textures from the floor. It does not see lighting, texture offsets, monsters, items
  or sound; the sliding door textures scored perfectly. Expect the user's first walk through these maps to find
  such things.
- A sized chest's width runs ALONG its `facing`, which every author read the other way; kept because the
  Temple's bookcases are tuned to it; a candidate for a format fix with a migration.
- The solver's gap widths (strides up to 144 at a walk) and its reach for using an event (160) come from reading
  the game's movement code, not from a run.
- S3's other deliverables: Goblinwatch and the Mad Necromancer's Lab, XD-05 (all started 16:45), the Temple of the
  Moon to 97 %, the user's walks of the Fortress and the held-out maps. Set-piece import and the Python port were
  dropped.
- S4's: New Sorpigal, Shadowspire, Vertigo Meadows; a sketch drawn from a description and not from an original.
