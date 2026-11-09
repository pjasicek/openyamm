# Handoff: city street performance work, stopped mid-way (2026-11-01 17:25, openyamm-06)

**Status (2026-11-01 evening): both tasks finished and verified.** Results: CITY_STREET_COST.md "Proposal 2: result"
and "Result of proposal 3", the ledger's "2026-11-01 evening" section. The notes below are the state at the stop.

Stopped at the user's request (usage quota at 99 %). Everything before this work is finished and recorded: the seven MM9
cities as BLVs open to the sky, daylight, MM9 fog, leaning ladders, the portal debug view (report at the top of
`overnight/dungeons_ledger.md`, `CITIES_ROLLOUT.md`, `CITY_STREET_COST.md`).

The user approved two optimizations from [CITY_STREET_COST.md](CITY_STREET_COST.md) (proposals 2 and 3). Two agents were
working on them and were **stopped mid-task**. Their state:

## 1. Merged roof-line portals (proposal 3), converter + city rebuilds: about 85 % done, unverified
- Converter change in `level_generation/projects/mm9r_common/city/` (`structure.py` / `hooks.py`, an opt-in setting
  for few large roof-line top portals per street room instead of ~1 370 small rectangles). Read the diff first.
- **Six of seven cities were rebuilt with it and reinstalled in the review root** (Guberland 16:32, Thjorgard 16:38,
  Thronheim 16:50, Drangheim 16:55, Sturmford 17:00, Arslegard 17:07). **Frosgard was not rebuilt** (still the 23:40
  build of the night; it has only 12 portals anyway, so it may not need it).
- Not done or not known to be done: every city's scenarios after the rebuild, the hole check (review tours after vs
  before; old sheets in each project's `review/`), the before/after counts per pose (portal faces, traversal nodes,
  portal tests, the 256-node cap: it was hit at 3 of 12 Thjorgard street poses before), and the docs (CITY_PLAYBOOK,
  READMEs, ledger city sections, CITY_STREET_COST "proposal 3 result"). The agent was re-running "before" counts and a
  second rebuild queue when stopped; it may have left scratch output in the city projects' `work/` folders and an empty
  `assets_editor_dev` folder beside an alternate asset root (harmless).
- Its converter lock (`locks/converter_edit.d`, owner "portals_1101") was released by the orchestrator after stopping it.
- **Next:** check that each city's overrides survived (half_steps, daylight, fog, bright_scale_lights, sky_fog,
  ladders), run every city's scenarios, the hole check, the counts (`tools/RUN_GAME.md` "Indoor portal view",
  `city_street_cost/portal_tour.yml`), decide Frosgard, update the docs. Lich Lab `--plan --scratch` must be identical.

## 2. Indoor world batches merged by texture (proposal 2), shared renderer: in progress, NOT verified
- Engine edits in progress: `game/indoor/IndoorRenderer.cpp/.h` and a new `game/indoor/IndoorFaceDrawGroups.cpp`
  (and probably `.h`), plus whatever else `git diff` shows under `game/indoor/` since the portal view
  (`IndoorPortalDebugView.*`, `IndoorRendererPortalDebug.cpp` are the previous, finished task). The agent was
  re-applying a cpp step when stopped.
- **The tree compiles, and `build/game/openyamm` was rebuilt from it at 17:25** (orchestrator's compile check). So the
  current game binary contains the unfinished batching code: **its rendering is not verified.** If anything draws
  wrong, this is the first suspect.
- Not done: the design check (what forces separate draws: lighting, fog, daylight, lightmap pages, scrolling/animated
  textures, x4/x2 tiers, surface materials, translucent/water, movers, decals, event-face highlights, picking), unit
  tests, pixel identity old vs new binary on MM6 6d02, MM7 7d06, MM8 d06 and d12, Lich Lab, Anskram Keep and
  Thjorgard City noon/night (method in `level_generation/projects/mm9r_common/daylight_fog_20261031/`; build the old
  binary from a copy), draw counts per pose before/after, the test suites (unit all, runtime 54/55 with the known
  braziers case, indoor 174/174), and docs.
- **Next:** read the diff, finish or back it out (do not use `git restore`/`stash` on the user's tree without asking;
  undo by editing), then verify as above. Goal: Thjorgard street world draws from 160–430 down to about 76–103 with
  identical pictures.

## Other state
- Two `openyamm --world mm9` processes were running at 17:22 (started ~17:19, probably the stopped agents' runs or the
  user's); not killed.
- Pending user decisions (unchanged): Arslegard as a living party, BrightScale for 12 dungeons, grey day sky in
  Thjorgard/Drangheim, the six swimming decisions (ledger report, top).
