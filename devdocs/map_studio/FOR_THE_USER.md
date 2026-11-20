# For the user (written overnight 2026-11-13/14)

**Overnight in short:** the six outdoor code batches from the 42-map survey (ways in, events and flags, fountains
and bridges, masses and roofs, land, landmarks) plus a roof batch are merged (309 unit cases, every playtest
passing); the four rebuilds are cleaned (z-fighting at or under their originals' counts) and use the new words;
Vertigo's pass three is inside every town-feel range by the numbers. Nothing was judged by eye: the display was off.
To play: `output/studio_play/PLAY.md` (Vertigo: `xeen_root`, `xeen_x1.odm`, mm7).

What the lead wants from you when you are back, newest last. Run commands for every map are in
`output/studio_play/PLAY.md`.

1. Commit when you like: the game's status-line duration change, the 22 lifted decoration bindings, and
   `tools/terrain_materials.py` (a tile without art takes coverage from its `shape_from` tile).
2. Xeen story review (`devdocs/xeen/reviews/STORY_AND_ATMOSPHERE.md`), your decisions:
   - May short original MM4/MM5 lines be quoted or closely paraphrased (the plan says rewrite all text)? The review
     says quoting is what keeps the atmosphere and avoids "slop".
   - Darkside: amber days with a weakening sun instead of "perpetual dusk" (the original has day and night).
   - Where Xeen stands beside the other worlds: a separate Ancient world from its own new-game card?
   - The goblin rules slate in XD-04 is ours, not the original's; keep it beside the original's skull lines?
3. Xeen scale review (`devdocs/xeen/reviews/SCALE_AND_DENSITY.md`, heatmaps in `output/xeen_review/scale/layer_*.png`),
   your decisions:
   - Small dungeons: the plan's "S" class (and XD-03, XD-05 as built) is the shipped M size; nearly half of shipped
     dungeons are short. Shrink S to the shipped band (MM7 median 8 rooms, 22 monsters), and XD-03/05 with it?
   - Six large set-piece dungeons against MM7's 4 and MM8's 2: cut to 4?
   - X1 Vertigo Meadows does the start map's and the hub's job at once (7 dungeons, the densest map measured). Move
     some of its dungeons and density to X2/X3, and add a road to the hub X2?
   - Monster bands per map role (start, hub, wilderness) instead of one band for all.
4. Xeen combat review (`devdocs/xeen/reviews/COMBAT_AND_PROGRESSION.md`), your decisions:
   - The plan's late game gives about 2.2x MM7's kill experience (party would finish near level 100): adopt the
     review's per-map table (about 4,100 monsters, about 6.3M party kill experience, level 62-65 as played)?
   - Split the ten monster families whose levels span far beyond MM6-MM8's 2-3x (serpents 5-45, swamp things 11-60...).
   - Use the MM6-MM8 treasure table, not MM9's plus a step; training caps 10/25/40/60/80/200/unlimited.
   - Act I ends at level 4-5 by its kills, not 10; the six built maps already sit on that curve.
5. Overnight the desktop display went away ("SDL_Init failed: The video driver did not add any displays"), so
   desktop runs and screenshots stopped; agents that need pictures waited or reported it. If you can, keep the
   display on (or unlocked) when you leave the agents working.
6. Data fix to approve (game data, so not applied without you): Tularean Forest (7out04) binds event 504 on the
   building `ClL1_W` (MMerge's Dimension Door) with no handler, so clicking it does nothing. The proposed handler
   for `7out04_mmmerge.lua` is in `output/studio_s4m/data_fix_7out04_504.md` (checked headless on a scratch mount).
7. With no display overnight, the six outdoor code batches (O-A to O-F, all merged) were checked by numbers against
   their shipped places, not by eye. When the display is back the lead takes the pictures of each place beside its
   original (lists in `output/studio_s4l..s4q/`) and the by-eye review of Vertigo's pass three; nothing needed from
   you except the display.

**Answered 2026-11-14:** original text (quote short lines), Vertigo's load (3-4 dungeons, the rest moved, a road to
X2), progression (the combat review's table adopted), dungeon sizes (S shrinks, 4 large). Recorded in
`devdocs/xeen/README.md`. Still open, smaller: Darkside's amber days, where Xeen stands beside the other worlds, the
goblin slate beside the original's skull lines (the lead assumes the reviews' proposals until told otherwise).
8. Xeen design documents updated to your decisions (2026-11-14; `devdocs/xeen/HANDOFF.md` §0,
   `devdocs/xeen/CHANGES_FOR_BUILT_MAPS.md`). Points that need you:
   - **X1's monster count conflicts.** The adopted progression table says about 130 hostiles for X1; after your walk
     ("monster packs are not that many") pass six measured the start maps (Harmondale 250, Ravenshore 196, New
     Sorpigal 96) and raised X1 to 208. The lead's view: your walk and the measured start maps win for X1; the
     table's experience budget is kept by lower levels, not fewer monsters. Agree?
   - Large set pieces: the table gives 70-80 monsters each; shipped MM7/MM8 large dungeons hold 120-180 (adds about
     two late levels). Raise to the shipped size?
   - X1 keeps four dungeon sites (Joe's, the mines, the Witch Tower, the orc caves) with the Deep Mine below the mines;
     the Temple of Yak moves to X2, the Dungeon of Death to X7; X2 and X3 swap places so X1's west road reaches the hub.
9. The game's `pin <text>` console command (2026-11-14, approved S5 game change) to commit when you like:
   new `game/debug/PinInbox.{h,cpp}`, `tests/PinInboxTests.cpp`, `tests/scenarios/console_pin.yml`; edits in
   `game/app/GameApplication.cpp` (shared `consolePartyPose()` for `loc` and `pin`), `game/app/GameSettings.{h,cpp}`
   (`[debug] pin_inbox_path`, default `pins_inbox`), `game/scenario/ScenarioRuntimeDriver.cpp`, `tools/run_game.py`,
   `tools/RUN_GAME.md`, `.gitignore` (`/pins_inbox/`), `game/CMakeLists.txt`, `tests/CMakeLists.txt`. Use: in a game
   run press the console key and type `pin the gate leaf flickers`; the pose, text and a screenshot land in
   `pins_inbox/` at the repository root.
10. One minute by hand for S5 spike 5 (automation cannot press browser shortcuts): run
    `node output/s5_spikes/1_viewer/host.mjs --port 8790`, open `http://127.0.0.1:8790/keys.html?prevent=1` in Chrome
    and in Firefox, press F5 and Ctrl K: the page must not reload, and its log must show "F5 (taken)" and
    "Ctrl+k (taken)". Tell the lead what happened in each.
11. A spike agent ran `npm install` in your home folder by mistake (2026-11-14 15:32). It removed what it added
    (`typescript` from `~/package.json`, `~/node_modules`), but `~/package-lock.json` was rewritten and now lists only
    `codex` and `node-fetch`. If you had a different lock file there, restore it; the state right after the mistake
    is copied in `output/s5_spikes/4_rpc/home_package-lock.json.after_npm`.

**Done 2026-11-14 17:32:** item 10 (Chrome: F5 taken, Ctrl K taken by the browser); item 11 (`~/package-lock.json` left: it matches `~/package.json`).
12. CI for the studio (`.github/workflows/studio.yml`, tracked, so not changed by agents): it passes
    `tests/fixtures/assets` as the asset root, with which the shapes_gallery step already fails (old binary too). The
    new 22-project native-against-wasm and sanitizer scripts (`openyamm-studio/tests/native_vs_wasm.sh`,
    `tests/sanitize.sh`) need `assets_dev` and the Xeen play root, which `output/` (git-ignored) holds. Decide whether
    CI gets those assets (or runs these on a self-hosted machine), or whether they stay local checks.

**Committed 2026-11-14 (by openyamm-03 for 2.4, local, not pushed):** items 1 and 9 (status-line durations, the 22 bindings,
`tools/terrain_materials.py`, the pin command) in d81e300cb9 and 4f9cbaf221; the Map Studio and Xeen records in fab2e72847
(without `briefs/mm7_7out03`, still in work). Left out: `openyamm-studio/`, `.github/workflows/studio.yml`, `output/`.

13. S5a4's game changes (2026-11-14, approved: the start-of-map console file and the exit pose), to commit when you
    like: `game/app/GameSettings.{h,cpp}`, `game/app/GameApplication.{h,cpp}` (also carries other sessions' edits;
    S5a4's are an include, `tp`, two methods, two hooks), `game/debug/ExitPose.{h,cpp}` (new), `game/CMakeLists.txt`,
    `game/scenario/ScenarioDocument.h`, `ScenarioYamlLoader.cpp`, `ScenarioRunner.cpp`, `ScenarioRuntimeDriver.{h,cpp}`,
    `tests/ExitPoseTests.cpp` (new), `tests/CMakeLists.txt`, `tests/scenarios/debug/play_here.yml` and
    `play_here_start.console` (new), `tests/scenarios/README.md`, `tools/run_game.py`, `tools/RUN_GAME.md`.
    **Please confirm two small extras the agent added beyond the approval:** `tp` takes an optional yaw (radians) and
    pitch (degrees), so Play here starts facing the browser's view; `tools/run_game.py --extra-mount`.

14. S5 is complete except what needs you (2026-11-15). Your decisions: (a) deploy the hosted page (the four things in
    S5.md "S5c": the studio in the repository, an origin, a publishing step, the download's default origin); (b) start
    S6 (MM9 profiles and extras) and/or S7 (consolidation: the game links the studio's core and `editor/` is deleted
    per EDITOR_RETIREMENT.md: a large change to the game); (c) optionally a performance pass on the missed hosted
    budgets (Chrome's first open, indoor commit p95 in the browser, outdoor 3D after a commit, the 2.98 MB core).
    Optional hands-on checks any time: `openyamm-studio/build-s4/oymap studio`, open the link, walk a map, pin it.

**Committed 2026-11-15 08:58 (openyamm-03, 2.4, local, not pushed):** item 13 (S5a4's game features incl. the `tp` yaw/pitch and `--extra-mount` extras) and the map_studio records in cf9638e72f and 73d14a8c46.

15. S7 plan written (14:03): `devdocs/map_studio/S7_PLAN.md`. Three things for you before the editor goes:
    (a) The plan builds the shared core library around the 44 shared game/engine sources where they stand (CMake only,
        objects checked byte-equal) instead of moving them into `core/` (moving rewrites 827 includes in 493 files; an
        optional follow-up, S7b). OK?
    (b) Deleting `editor/` loses, with no replacement: hand editing of faces in the old GUI, OBJ/GLB model import,
        new-map creation in the old editor, mesh-to-metadata seeding and the editor's own regression suites. No script
        was found relying on them. Confirm that is fine.
    (c) Your local MM9 rebuild scripts (`output/mm9_rework/final_r*/r*.sh`) build the target `openyamm-editor`, and the
        MM9 orchestrator handoff tells the next run to copy them: they will need the new build line (the plan lists it).

16. S6's game changes (14:39; details in `devdocs/map_studio/S6_PLAN.md` and S5.md "S6"), none made, each needs your yes:
    G1 scene overlays may carry ladders (small); G2 cinematics overlays merged by cinematic id (small); G3 named mods in
    the game: `mods/<id>/mod.yml`, an enabled list, a switch (Mods page or console), table contributions, id-range
    checks (medium; this is S6's exit "a mod switched off in the game"); G4 move the cinematic library parser into its
    own file so the studio can use it (move only, small); G5 overlays may add actors and items (medium: base actor
    indices and saves).

**Answered 17:58:** item 15: shared sources kept in place; the old editor's GUI-only features may go; the S7 agent updates the local MM9 rebuild scripts. S7 now runs through step 6 (deleting `editor/` last).

**Answered 20:10:** item 16: all five approved (G1-G5), on condition that nothing existing breaks. In progress (new lead,
two agents: G1/G2/G4/G5 and G3); checked against a frozen baseline of the post-S7 game (`output/studio_lead/g/`:
unit tests, release and MM9 scenarios, the MM6-8 regression suites, every studio playtest, load times).

17. S7 done (19:50), for your commit (nothing staged). Tracked, modified: `.github/workflows/packages.yml`, `.gitignore`,
    `AGENTS.md`, `CMakeLists.txt`, `COPYRIGHT`, `README.md`, `android/app/build.gradle`, `cmake/BgfxRuntime.cmake`,
    `packaging/rehearse_release.py`, `devdocs/map_studio/{EDITOR_RETIREMENT,PLAN,README,S7_PLAN}.md`,
    `devdocs/mm9_rework/HANDOFF_20261107_ORCHESTRATOR.md`, `devdocs/mm9_rework/overnight/AGENT_BRIEF.md`,
    `engine/AssetFileSystem.{cpp,h}`, `engine/CMakeLists.txt`, `game/CMakeLists.txt`, `level_generation/PIPELINE_STATUS.md`,
    the 18 repointed callers and their READMEs under `level_generation/projects/{brackenford_greywatch,hesper_out1-4,
    mm5_castleview_kalindra,mm9r_common,mm9r_isleofashes}/` and `level_generation/terrain/`, `tests/CMakeLists.txt`,
    `tests/ImageAssetLoaderTests.cpp`, `tests/IndoorSourceGeometryCompilerTests.cpp`, `tools/CMakeLists.txt`,
    `tools/PERF_PROFILING.md`, `tools/VULKAN_DLSS_TEST.md`, `tools/mm9_compile_indoor_source_main.cpp`. Deleted: all 61
    files under `editor/` (16 moved to `core/compile/`), `res/editor_1.webp`, `res/editor_2.webp`, the two editor shaders
    in `game/shaders/`, `tools/mm9_import_discovery/run_mm9_active_gate.sh`, `assets_dev/worlds/mm8/maps/out01.{map,
    geometry,terrain}.yml`. New: `core/CMakeLists.txt`, 19 files in `core/compile/`, `third_party/cgltf/`. The commit needs
    `openyamm-studio/` as well (untracked; the repointed callers and docs use it). Not S7's (leave out of it):
    `game/debug/MawTestParties.*`, `game/gameplay/GameplaySpellService.cpp`, the MAW test parties yml, `settings.ini`,
    `devdocs/maw/README.md`, `devdocs/solo_action/README.md`. You may delete `.openyamm-editor.ini`.

18. G1-G5 done (22:05), for your commit (nothing staged); checked against a frozen post-S7 game with no difference (S5.md
    "S6's game changes G1-G5"). New: `game/content/NamedMods.{h,cpp}`, `game/gameplay/CinematicLibrary.{h,cpp}`,
    `game/gameplay/GameplayWorldPoint.h`, `tests/SceneOverlayTests.cpp`, `tests/NamedModsTests.cpp`,
    `tests/scenarios/scene_overlays/`, `tests/scenarios/mods/`, `devdocs/NAMED_MODS.md`. Modified: `engine/AssetPackIndex.h`,
    `engine/AssetFileSystem.{h,cpp}`, `game/data/GameDataLoader.{h,cpp}`, `game/app/GameApplication.{h,cpp}`,
    `game/scenario/{ScenarioDocument.h,ScenarioYamlLoader.cpp,ScenarioRunner.cpp}`, `game/gameplay/CinematicRuntime.{h,cpp}`,
    `game/gameplay/GameplayRuntimeInterfaces.h`, `game/maps/SceneOverlayPaths.{h,cpp}`, `game/maps/IndoorSceneYml.{h,cpp}`,
    `game/CMakeLists.txt`, `core/CMakeLists.txt`, `tests/CMakeLists.txt`, `tests/AssetFileSystemTests.cpp`,
    `tests/scenarios/README.md`, `AGENTS.md` (one line: named mods), `packaging/MODDING.md`,
    `devdocs/{SAVED_MAP_STATE_IDENTITY,INDOOR_ROTATING_MOVERS_AND_LADDERS}.md`, `devdocs/mm9_rework/MM9_CUTSCENES.md`,
    `devdocs/maw/MM9_BALANCE_DESIGN.md`, and in `openyamm-studio/` (untracked) `core/{Cinematics,Mods}.{h,cpp}`,
    `tests/S6Tests.cpp`, `README.md`, `schema/{objects,mod}.schema.json`. Shared with S7's uncommitted edits (one
    commit is simplest; splitting needs hunks): `engine/AssetFileSystem.{h,cpp}`, `core/CMakeLists.txt`,
    `game/CMakeLists.txt`, `tests/CMakeLists.txt`, `AGENTS.md`.

19. S8 done and merged (2026-11-16, merges 37-39; S8_PLAN.md) and the five new Xeen maps installed (X2, XD-21, XD-27,
    XD-06, XD-12; `devdocs/xeen/ACT2_BUILD.md`; play commands in `output/studio_play/PLAY.md`). Nothing staged; the
    studio is untracked (`openyamm-studio/`), the Xeen briefs are under `devdocs/xeen/briefs/`. Game changes found on the
    way, none made, each needs your yes:
    - Placed monsters: the scene's own hit points are ignored and the own name shows only on the corpse (every boss:
      Darzog 1,200 in the scene, 400 in play; the Robber Boss; the Yak Master); boss rows in monster data would do it too.
    - A no-magic map's refusal says "You can't do that while underwater" (XD-12).
    - The game reads only one `--extra-mount` (every Xeen agent combined mounts by hand).
    - Model water faces drawn as level (normal 0,0,1 in `OutdoorRenderer.cpp`: upright falls streak, no falling-water
      foam), always opaque, hairlines where water faces meet at an angle (Alvar too), flow time never wrapped (S8e).
    - Scenario runner: `triggered_event: 0` for decoration events (`IndoorRenderer.cpp` ~5727), `status()` loses step
      lines, `setup_shortcut: {kind: grant_item}` does nothing, event exits leave no transition trace.
    - MM9: a new map cannot join `openAirMaps` (spells follow indoor rules there); the installed
      `worlds/mm9/terrain_materials/world.yml` lacks `cliff_layered` and `snow`; headless runs load no terrain
      materials; `parseTerrainMaterialConfig` is not in the shared core list (S8b).
    - A windowed run of an outdoor map without a terrain material file fails to start (S8g).
    - Still open from item 16's helpers: ladder stepping out of `IndoorPartyRuntime` (the browser's walk climbs);
      bakes honouring `--extra-mount`.
