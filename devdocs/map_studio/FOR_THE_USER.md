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
