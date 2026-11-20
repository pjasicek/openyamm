# MM9 cities as native BLVs: rollout brief (2026-10-31, openyamm-06)

The user decided (2026-10-31) that MM9's seven cities become **BLV maps open to the sky** (performance: walk-in houses
are sectors behind door and window portals), and asked this session to convert all of them while they are away. The
Sturmford City pilot is done and accepted by the orchestrator: [its record](../../level_generation/projects/mm9r_sturmfordcity/README.md).
This brief is for the agents converting the other six, one city per agent.

| City | DAT (`mm9/extracted/WORLDS/WORLDS/`) | Size | Wave |
| --- | --- | --- | --- |
| Thjorgard City | `THJORGARDCITY.dat` | 9.4 MB (largest: check the 65 535-vertex limit early) | 1 |
| Thronheim City | `THRONHEIMCITY.dat` | 7.7 MB | 1 |
| Drangheim City | `DRANGHEIMCITY.dat` | 4.8 MB | 1 |
| Arslegard City | `ARSLEGARDCITY.dat` | 4.0 MB | 2 |
| Frosgard City | `FROSGARDCITY.dat` | 4.7 MB | 2 |
| Guberland City | `GUBERLANDCITY.dat` | 4.5 MB | 2 |

## Read first, in full
1. [CITY_PLAYBOOK.md](../../level_generation/projects/mm9r_common/CITY_PLAYBOOK.md): the recipe.
2. [DUNGEON_PLAYBOOK.md](../../level_generation/projects/mm9r_common/DUNGEON_PLAYBOOK.md): every step and gotcha applies,
   including its lock rules.
3. The Sturmford City project (`level_generation/projects/mm9r_sturmfordcity/`: README, `convert.py`, `overrides.yml`,
   `citylua.py`, `make_tour.py`, `make_scenarios.py`) and its props project (`level_generation/props/mm9_sturmfordcity_claude/`).
   Copy its structure; do not import from another city's project.
4. [MM9_LIGHTING_DECISION.md](MM9_LIGHTING_DECISION.md): classic lighting, **no bakes**.

## Deliverables per city
- `level_generation/projects/mm9r_<city>/` with a README in the Sturmford form: numbers and limits, structure table,
  sky and minimap, content, scripted objects table, quality gates, performance counts, open items.
- The map installed in the review root `output/mm9_rework/assets_dev` (through `review_root.install`), its rows in the
  shared tables (under `review_tables.lock`), transitions both ways (the wilderness map, sewers, Town Portal).
- Review sheet: old ODM import | native BLV, at least 24 eye-level views (streets, plazas, every kind of interior), and a
  sky sheet at four times of day. Look at every image yourself; holes, wrong sectors or missing faces block acceptance.
- Scenarios with real clicks where the engine picks: doors and exits, shops (at least two walk-in shops by dialogue),
  chests, scripted objects (quest rewards, key setters). All must pass.
- Performance counts on the same views as Sturmford (draw calls, triangles, sectors drawn, map load) against the old ODM
  import. Frame rate is not measured (needs a single-session run).
- A section in `devdocs/mm9_rework/overnight/dungeons_ledger.md` ("<City> City") and one line in `STATUS.md`.

## Rules
- Lock files are in `level_generation/projects/mm9r_common/locks/`. Converter code (`mm9r_common/`, including `city/`)
  is shared with other agents: change it only while holding `locks/converter_edit.d` (`mkdir`, write an `owner` file
  with your city name, `rmdir` when done; wait if it exists), keep every change opt-in or provably neutral, and check
  that Lich Lab `--plan --scratch` and Sturmford City's `--plan` stay identical. City-specific behaviour goes in your
  project's `overrides.yml` / `convert.py`. C++ builds only inside `flock -x .../locks/cmake_build.lock`; shared mm9
  tables inside `mm9_decorations.lock` or `review_tables.lock` as the playbook says.
- Engine changes: only when the city cannot work without them, opt-in per map, with tests. After every engine build:
  `openyamm_unit_tests` all pass, `openyamm_runtime_tests` 54/55 (the New Sorpigal braziers case fails already) and the
  `indoor` regression suite 173/174 (`mm6_ogr_actor_models_bind_all_tiers` fails already). Nothing in MM6–MM8 may change.
- If a city exceeds 65 535 vertices: report to the orchestrator before widening anything (the playbook's spec says how).
- Stop and report instead of guessing when a city cannot work as a BLV, or a fix would change MM6–MM8 behaviour.
- Never run `git add`, `commit`, `stash`, `reset`, `restore --staged`; never push. No Vulkan builds, no Android cooks.
- Safe deletes: `ls` first, then `rm` with literal paths only (a hook refuses `$`, `*`, `?` and backticks); never
  anything under `/dev`.
- Never kill a process you did not start; wait on your own PIDs (`kill -0 <pid>`), never `pgrep -f`.
- Every game launch starts with `SDL_AUDIODRIVER=dummy`; use `--isolated` with a unique name (`city_<city>_...`).
- Do not edit Lua files headed `-- generated from legacy EVT/STR`, MM6–MM8 data, or `assets_dev/engine` (except
  decoration models and bindings per the playbook).
- Peak memory is about 2 GB per conversion (Thjorgard maybe more); up to four agents run at once.
- Durable notes in the repo (the project folder), not /tmp.

## Shared findings (orchestrator updates this section)
- **Raised floors (settled 2026-10-31, CITY_PLAYBOOK.md "Raised floors")**: set `half_steps: true` in overrides.yml's
  `city` block and rebuild. The party steps 50; the pass adds invisible half steps only up 50-66 rises the party can
  stand on. Most audit "unreachable" regions are building plinths, solid blocks, counters, table hulls and basins
  (Sturmford: all 18), which need nothing: say so in your README. Probe each step in `build_report.json`
  `stats.city_half_steps`; a standable floor 67-127 high needs a hand-made ramp.
- Townsfolk draw as stand-in peasants until the MM9 town NPC models exist (another session's work); not your job.
- **Daylight and fog in open-sky cities** (orchestrator, 2026-10-31): Thjorgard City's streets came out much darker and
  hazier than MM9's (classic sector ambient only; MM9's `Fog0` applied automatically looks far denser than its
  64..11 520 range). A separate agent is building the systematic fix (daylight for open-sky sectors by time of day,
  MM9's fog by day and night). City agents: do not change lighting or fog yourselves; the fix will be applied to every
  city afterwards.
- **Daylight and fog settled (2026-10-31, CITY_PLAYBOOK.md "Daylight and fog")**: set `map: {fog: lithtech}` and
  `city: {daylight: true}` in overrides.yml and rerun `convert.py` (the BLV is unchanged, only the scene gains
  `daylight` and the fog's `model`/`night`). Streets open to the sky then take MM9's ambient and its StaticSunLight by
  the time of day, interiors stay as they are, nights are dark; the fog follows MM9's own model (view depth, two passes)
  and its WeatherMan night state. Thjorgard and Sturmford City are reinstalled with it. Frosgard City's dense grey fog
  is MM9's own (1-2 000 LT, FarZ 2 500); its sky would be grey too in MM9 (`SkyFog`, not carried).
- **Rolled out, street lights, sky in fog (2026-10-31, late; CITY_PLAYBOOK "Daylight and fog", "Street lights and
  BrightScale")**: Frosgard, Thronheim and Guberland City now have daylight and `fog: lithtech`; all five rebuilt
  cities (and Sturmford, Thjorgard) have `map: {bright_scale_lights: true}`: BLV light colour x MM9's BrightScale, as
  MM9's lightmap bake used it (the runtime never reads it). Sturmford's yellow-white facades are gone. **Drangheim and
  Arslegard City: add `bright_scale_lights: true` at the next rebuild.** Frosgard City also has `map: {sky_fog: true}`:
  MM9 draws its sky box wholly in the fog colour whenever its fog's SkyFogNearZ is nearer than the box, so Frosgard's
  sky is 127 grey (engine opt-in: scene fog `sky`). By their DAT, Thjorgard and Drangheim City would be grey-skied by
  day too (not set: the orchestrator's call). Screenshot tours: one view per game run (`daylight_fog_20261031/
  compare_tour.py`); long BLV tours end in a death video. MM9's world fog turned out to be range fog, not view depth
  (INDOOR_FOG.md "Correction"; `model: lithtech` not changed). All scenarios of the five cities pass.
- **Tour deaths fixed, last BrightScale rebuilds, night fog (2026-11-01; CITY_PLAYBOOK "Daylight and fog")**: the
  death video at the end of long city tours was the tour, not the cities: the indoor renderer ran the game clock while
  the tour held gameplay, so each repeated `time:` jumped a day, and after four days without rest the ordinary
  days-without-rest rule killed the party (at full HP). Players cannot get there. Engine fix on the debug path only:
  the tour holds the indoor clock (doors still move) and its clock jumps do not count as days without rest; long tours
  (16 and 32 shots) now end alive and need no one-view-per-run split. Drangheim and Arslegard City now have
  `bright_scale_lights` (all seven cities do). Cities with daylight and fog (Thjorgard, Drangheim, Frosgard) get scene
  fog `follow_daylight` from the converter (`city/hooks.py`): the fog and a fogged sky darken with the daylight
  (noon unchanged), so Frosgard's night sky is no longer light grey. Rebuilt: Drangheim, Arslegard, Frosgard, Thjorgard.
