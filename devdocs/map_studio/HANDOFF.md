# Map Studio handoff

Kept current by the lead session; the user asked on 2026-11-13 for an update every 30 minutes while work runs. The
block "Status" below is rewritten each time; the rest changes when a fact changes.

Read this first, then `S3.md` from "Round three merged" to "WebAssembly" (the record of what was built and
measured, round by round), `REBUILD_PROCEDURE.md` (dungeons), `OUTDOOR_REBUILD_PROCEDURE.md` (outdoor maps),
`rounds/ROUND_FOUR.md` (how a round's common brief looks) and `openyamm-studio/README.md`. Older: the first part of
`S3.md`, `S2.md`, `S1.md`, `S0.md`, `PLAN.md`.

## Status (2026-11-13, 12:07)

**Eighth merge (11:20), with one correction (about 11:45).** `build/oymap` holds the indoor code agent's fix of the
user's Forge faults (`output/studio_obj5/`) and outdoor code batch six (`output/studio_s4g/`); binary before it:
`output/studio_lead/oymap_before_merge8`. S3.md "Eighth merge" has the detail. First checks: 210 unit cases, shapes,
slice, rewire pass; builds differ only as the merge says; every indoor and Xeen playtest four of four except **Castle
Darkmoor 0 of 4, caused by the merge**: sideways leaves travelling 2 past the jamb leave the game no way through the
open doorway (proved on its stair door). The lead reverted that for sideways leaves (`overtravel` in
`IndoorLowering.cpp`; unit cases changed; 210 pass; binary between: `oymap_merge8a`). Re-check
(`merge8/recheck.sh`): slice and rewire pass; Harmondale and Ravenshore as round four found them pass with old and
new binary alike (their failures were round four's edits in progress); **the shapes walk passes but its audit fails
on three `geometry.coplanar` findings** (sideways leaves' free edges in the jamb's plane when open, which the
overtravel had hidden): given to code batch nine. Every playtest again in `play2.out` (the Fortress and the Forge
four of four so far). XD-03's vault chest moved 24 east to fit the default chest size. The Forge in the user's copy
is rebuilt with the corrected studio once `play2.out` is complete.

**What the merge gives:** `switches[].kind: lever|button` (the originals' 3D handles and pushed blocks, their own
door records), switch pictures that follow a toggle's state and an event's branch, `chests[].kind` (end, middle,
end), things over movers standing on them at the start, `geometry.coplanar` in `build` and `audit`, things on walls
refused when they straddle a corner strip, `oymap things` and `calibration/things_shots.py`, `floors[].kind:
liquid`; outdoors: hidden slopes over flights (`parts[].climb`), upper-storey `band` and bay widths, `ground[].line`,
ridges two wide on diagonals, `scatter[].id`, hanging signs, blank structures, the rim's eyes 4 cells inside the
square (rim part Harmondale 86.25 to 90.32, Ravenshore 78.94 to 88.17; totals 89.16 and 92.09, projects unchanged).
REBUILD_PROCEDURE.md "What the measure does not see" names the new tools.

**Applied by the lead:** the Forge (26 levers, lever 3 the original's `BemH16c` arm on a `6voltyl` plate, chests by
kind; backup `output/studio_cal/mm6_6d18/merge8_backup/`), installed again in the user's copy
(`output/studio_play/forge_root`); the lead's pictures at the user's two poses match the original's (one chest's
carved lid `ch3tpbv` is not a kind's choice yet: NEXT_CODE_BATCH.md 13). The Temple of the Moon's two buttons
`kind: button` (backup `output/studio_cal/mm7_7d06/objects_before_merge8.yml`). The running agents were told their
maps' lines; the Hive, Fortress, Lincoln and Xeen projects need none beyond what the merge does.

**Finished 11:36: Control Center's round six** (99.2 to 99.4 %; shape 99.7, textures 98.2 to 98.9; playtest 267 steps
four of four on the final build; 64 of 71 events as the original's, the other 7 bound to nothing in the original;
terminals as message windows; all 21 doors fold at the original's widths, thresholds and girder reveals; the 14
chests had stood 9 to 48 off (the front's middle read as the box's centre) and now stand at the original's places,
`kind: ch5`; the button `kind: button` with its face `SWr4` (the lead's message had named the block's top); edge
agreement of 132 pairs 0.754 to 0.817). Gaps item 14 of NEXT_CODE_BATCH.md. **Castle Darkmoor's playtest fails on
the merged build every run** (step 70, a walk stuck at (10284, 11493, 267)); its agent is editing the project, so
the lead is running the project as the round found it with the old and the new binary to see which causes it.

**Finished 11:52: Castle Darkmoor's round six** (99.1 to 99.2 %; 267 rooms; playtest 211 steps four of four, the
forcefield now checked by walking; 50 of 54 events as the original's; doors fold at the original's widths, levers
`kind: lever` in their niches, chest `kind: ch2` with the original's roll levels, sarcophagi with their question,
signs as message windows; no faces in one plane left, the original has 3; edge agreement of 64 pairs 0.783 to
0.838). Every door folds, so the sideways-leaf correction does not touch it. Gaps item 15 of NEXT_CODE_BATCH.md.

**Finished 11:58: the Abandoned Temple's round six** (96.5 to 96.9 %; shape 97.0, textures 95.3 to 96.6; playtest 252
steps 16 of 16, the last four on the merged binary; the step-175 failure explained: the scenario party is one
character with one pack, and the idol needs a free 2x4 block; door leaves show their whole carved pictures, fold
against the lintel, tile their rock; secret doors pulse; chests trapped with the original's roll levels; leave
events; 84 of 94 events as the original's). It corrected the lead: the 8 switches are the original's flat trap
plates (`t65b11b`), while the `T65A13A` blocks are the 46 maze buttons, already movers of that form. **Worst
finding: right after arrival the party's eye is outside the sector of the platform it stands on, and the view is
black in every direction** (`output/studio_cal/mm8_d05/ingame_r6/arrival/sheets/03-box-top-north.png`); given to
code batch nine as its first item, a check for every map. Gaps item 16 of NEXT_CODE_BATCH.md.

**Finished 12:07: outdoor round four** (Harmondale 89.16 to 89.21 %, without the rim 86.21 to 86.24; Ravenshore 92.09 to
92.20 %, without the rim 91.41 to 91.52, events 98.17 to 99.39; walks 63 and 136 steps, two of two twice each).
Harmondale's dais is climbed on foot by its north flight. The agent did not apply batch six's `climb` rings: the
original's dais has steps only on its four flats and a parapet on each diagonal, so it redrew it as the original
(octagon, four `stairs`, four parapets, trap 432 square). Scatter ids and seasons corrected against the original
(three branches, as its event 250). Ravenshore: Needful Things on its terrace with its door there; the deck and
terrace cut round their stairwells from the original's faces; ships clicked on their cabin doors. Wrong building
forms found in 280 pictures of interactive things are outdoor item 8 of NEXT_CODE_BATCH.md.

**Finished this morning** (S3.md has each): the Forge's finishing round (99.7 %), the Temple of the Moon's round six
(95.9 %), Warlord's Fortress to L4 (99.7 %), XD-03 from its brief, both Xeen texture passes, the Hive's round six
(97.7 %), the user's walk through the Forge and his look at XD-01's textures (both made rules in
REBUILD_PROCEDURE.md).

**Running: three agents on Opus** (the user allows six; code batch nine, XD-04, outdoor code batch seven). Their results are NOT read while this block names them as
running:

| Agent | Works in | Scratch | Delivers |
|---|---|---|---|
| Indoor code batch nine; started 11:53 | `openyamm-studio/`, builds only into `build-fix` | `output/studio_obj6/` | first a check that the party's eye stands in the sector of the top it stands on (the Abandoned Temple's black arrival view) and the sideways leaves' edge flicker that fails the shapes audit; then spawn groups (the Lincoln's chance failure), door frames (jamb and reveal surfaces, a leaf's free edge, top and ends), texture offsets seen by `compare`, chest lid variants, one face of a platform, an indoor sprite word, `ids.lock.yml` defects, `solve` and `things` defects, `panels[].secret`; playtests of every changed project four times |
| XD-04 the Witches' Tower from its brief; started 11:53 | `devdocs/xeen/briefs/xd04/L4/` | `output/studio_cal/xd04/` | a playable L4 under the texture and interactive-things rules, playtest four of four, NOTES.md, pictures `shots/` |
| Outdoor code batch seven; started 12:07 | `openyamm-studio/` (outdoor files), builds only into `build-s4` | `output/studio_s4h/` | outdoor item 8 of NEXT_CODE_BATCH.md: outdoor `things`, the outline/shape and assets defects, scatter placement independent of earlier entries; building forms the kits lack (round halls and huts, pavilions, porches, hips, steps, wall signs, railings, crenellation, wells, a hole in a part, a cave mouth), most common first; light inside buildings |

**Next, in order:**
1. When `merge8/play2.out` is complete: record it, chase any failure, rebuild the Forge into the user's copy with
   the corrected studio, regenerate the review page (`calibration/review_page.py`).
2. When code batch nine reports: check its pictures (the Abandoned Temple's arrival view above all), merge by
   "Merging" below (every playtest four times: the last merge's failure was a door), and give the projects its
   lines (the Lincoln's spawn groups, door frames, offsets).
3. When XD-04 reports: check, play, review page. When outdoor code batch seven reports: merge with batch nine (they
   share the tree), then outdoor round five applies its lines.
4. Next rounds, each starting from "What the measure does not see" and `oymap things`: the Lincoln round six (after
   spawn groups), Warlord's Fortress round two (item 11), the Temple of the Moon and the Hive looked at again with
   the new words; XD-05 from its brief.
5. Questions for the user, open: the Forge's lava (the original's timer only, or the shipped overlay's lava flag
   too); generating the 26 textures the Xeen projects list; what "within bands" means for the milestone; whether to
   drop set-piece import and the Python port; a git snapshot of `devdocs/map_studio` and `devdocs/xeen` (openyamm-a7
   left them uncommitted at the 2.3 commit `f4a6b80327`).
6. For the user, game-side: `monsters[].hp` ignored by the game (XD-01's boss, XD-03's King); names need
   `place_mon.txt`; MM7 has no ambient sounds and refuses the engine's `lava loop.wav`; an outdoor model shown by an
   event stays unclickable; after `SetFacetBit` by cog the use key reaches through a shut door; headless runs plan
   monster paths inside the frame (very slow walks beside tall blocks); scenario-runner faults (`open_door` kills
   nearby monsters, pulsing lights read `unset`, map timers stop in tours, and those in NEXT_CODE_BATCH.md "Not
   studio work").

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
| S3 indoor authoring | **in work.** Vocabulary far past the plan's list. Acceptance not met: Warlord's Fortress reached L4 (99.7 %, 2026-11-13), Goblinwatch and the Necromancer's Lab are not started, the "bands" are not defined against `oymap compare` scores, XD-01 to XD-03 are built from their briefs and play, XD-04 and XD-05 are not; set-piece import and the Python port are not started | `S3.md` |
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
| Control Center (MM6 sci-fi.blv) | `mm6_scifi` | 99.4 % | six |
| Castle Darkmoor (MM6 cd2.blv) | `mm6_cd2` | 99.2 % | six; 267 rooms |
| The Hive (MM6 hive.blv) | `mm6_hive` | 97.7 % | six; 100 rooms |
| The Lincoln (MM7 7d23.blv) | `mm7_7d23` | 97.5 % | five |
| Abandoned Temple (MM8 d05.blv) | `mm8_d05` | 96.9 % | six; all 112 moving parts; black view at the arrival (studio) |
| Temple of the Moon (MM7 7d06.blv) | `mm7_7d06` | 95.9 % | six |
| Warlord's Fortress (MM6 6d16.blv) | `mm6_6d16` | 99.7 % | one (L3 to L4, 10:28) |

Outdoor: the same folders, by OUTDOOR_REBUILD_PROCEDURE.md. Their first sketches were written from the originals
by scripts (`output/studio_s4c/gen/`; not run again) and then worked over by one rebuild round each; scores are
the lead's measurement of 2026-11-13, 01:35, with the stricter decorations part. They show what the builder can build from a careful description of
a known map, not yet a map from a written brief.

| Map | Key | Score | State |
|---|---|---|---|
| Ravenshore (MM8 out02.odm) | `mm8_out02` | 92.20 % (91.52 without the rim) | four rebuild rounds |
| Harmondale (MM7 7out02.odm) | `mm7_7out02` | 89.21 % (86.24 without the rim) | four rebuild rounds; the dais climbed on foot |

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
- S3's other deliverables: Goblinwatch and the Necromancer's Lab, XD-04 and XD-05, set-piece import, the Python
  port.
- S4's: New Sorpigal, Shadowspire, Vertigo Meadows; a sketch drawn from a description and not from an original.
