# ruinedtemple — overnight status

- Phase: DONE (2026-10-31 round 3: model lighting for props, teal pools fixed, darkness checked)
- Last step done: README (level_generation/projects/mm9r_ruinedtemple/README.md), props README, playbook row + lessons.
- Next step: none. Blockers: none. No converter or engine change; no BUILD REQUEST.

## Summary

- Faces 3 724, rooms 9 (+ sector 0), portal faces 10, movers 54 DAT models / 44 groups / 66 mechanisms, lights 65
  BLV (+2 bake-only), decorations 68, chests 3, actors 15 (14 monsters at MM9 body size + the hidden genie).
- Scenarios: doors_exits PASS (47 steps), chests PASS, scripted PASS (205 steps; real clicks on doors, buttons, dirt
  plugs, chests, Tree of Life, lamp, genie), work/reach_ramps.yml PASS (shaft bottom -> stair -> ramps -> tunnel),
  work/reach_monsters.yml PASS (Dagrell1, Skeleton2, SpectreDagrell0 close on the party).
- Brightness: MM9 mean 36.0, ours baked 34.3 (-4.7 %), unbaked 55.1. Views off by > 10 %: e01 e02 e03 e04 e05 e06 e07
  t01 t03 t05 s03 s04 s05 s06 n01 n02 n05 c01 c03 c04 c05 d01 d03 (12 of 34 within 10 %; skylight hall darker: MM9's
  sun through the skylight; crypt level brighter: white fills). Hue on the DAT lightmaps: G/R 0.85-1.04 of MM9's,
  B/R chroma 0.45-0.84 of MM9's. `stale_bakes.py --check` does not list the map.
- Unmatched scripted objects: TriggerHostile0 / DBEffectsTrigger0-2 (dust + quake effects only; not built);
  PropAnim.scr "onside" on the pews (no such animation in MM9's model).
- Sheets: level_generation/projects/mm9r_ruinedtemple/review/v06_compare.jpg (34 views, MM9 | baked),
  review/v01_compare.jpg (unbaked), review/lighting_compare.jpg (MM9 | unbaked | baked), review/flames/ (torch and
  chandelier flames from the sides); props: level_generation/props/mm9_ruinedtemple_claude/review/props_sheet.png.
- Not checked: perception hints on the desktop at Perception 8 (headless only: the tour party's hints show faintly);
  the genie's item and attribute wishes (gold tested); the lift ridden on the desktop (headless only); walking into the
  crypt hole after the lid falls (the scenario sets the party on each plug); TriggerCaveIn1 entered by walking (set_pose); actor art (3 placeholders).

## Pause handoff (orchestrator pause request)

- The map was already finished when the pause arrived: no bake, build or game run of this map is running, no lock is
  held (converter_edit.d not taken; flocks released), no half-written file.
- Verified: everything in Summary above. Built but unverified: only the "Not checked" items above.
- On resume nothing is required. Optional follow-ups (open decisions, none blocking):
  - Sun through the skylight (MM9 `StaticSunLight0`) for the darker skylight views: a bake-only light, then
    `level_generation/projects/mm9r_common/bake_slot.sh python3 level_generation/projects/mm9r_common/dungeon/lighting.py level_generation/projects/mm9r_ruinedtemple`
    and a new tour (`make_tour.py v07`, run_game.sh command in the README).
  - Desktop checks of the "Not checked" items.
- If `convert.py` is rerun for any reason, rebake (command above) and rerun the scenarios
  (`make_scenarios.py`, then the loop in the README).

## Lighting follow-up (lightmap-matched, v07)

- Profile `mm9_ruinedtemple.yml`: direct 5.0, bounce 3, ambient 0.55, sky 1.2; BLV light colours = colour x BrightScale,
  blue torches' green x0.5, white fills x0.25 (convert.py `blv_colour`); full rebake done, stale check clean,
  scenarios doors_exits / chests / scripted rerun: PASS.
- Per-zone luma ours/MM9 (work/lightmap_ratio.txt): entrance 1.16, south ruins 0.93, main temple 1.05, east rooms 1.10,
  north corridor 0.99, pew hall 1.15, elevator room 1.42 (smallest zone, too green), crypt level 0.98, shaft/ramps 0.94.
  B/R and G/R within ~15 % except the elevator room. Screen mean 32.2 (capture 36.0, not a reference).
- Sheets: review/v07_compare.jpg, review/lighting_compare.jpg (capture | unbaked | v07 baked), looked at.
- Decorations under the bake: much darker than the walls (decoration/wall: banners 0.25-0.35 baked vs 0.88-1.29
  unbaked, crate 0.62 vs 1.36, pews 0.18 vs 0.34; work/decoration_vs_wall.txt): not lit by the bake (sector ambient +
  point lights). Engine issue, reported, not fixed.
- No process running, no lock held.

## Round 3 (2026-10-31): props, teal, darkness

- Props: `map: {model_lighting: {light_scale: 4.0}}` kept (scene only). Compared on 11 prop crops against the old
  capture (work/model_lighting_props.txt): old path 0.14-0.88, old path + sector light 31 0.39-1.02 (but the crypt lid,
  a vertex-lit mover, 0.88 -> 0.59), model lighting x1.67 0.36-0.89, **x4 0.39-0.95** (banners 0.40-0.41, lamp 0.95,
  chests 0.58, crate 0.39, barrel 0.46, pews 0.46-0.47, podium box 0.57, sarcophagus 0.86). Decoration / wall back to
  the unbaked relation (banners 1.08 / 0.82, crate 1.04).
- Teal: lightmap G/B per zone now matches MM9 (mean 0.59-0.76 vs 0.62-0.78, brightest 5 % 0.54-0.84 vs 0.57-0.84;
  work/teal_check.txt): the torches' green 0.5 -> 0.3 in blv_colour (the pools clipped blue and kept green). Rebuilt and
  fully rebaked; e04/e05/e07/t02 read blue.
- Zones luma ours/MM9: entrance 1.08, south 0.86, temple 1.00, east 1.00, north 0.91, pew hall 1.04, elevator 1.22,
  crypt 0.93, shaft 0.88 (work/lightmap_ratio.txt).
- Darkness: min view luma 16.6 (the cell), none under 10-12; no player-light floor needed.
- Stale check clean; scenarios doors_exits / chests / scripted and work/reach_*.yml rerun: PASS (make_scenarios takes the
  exit id from the DAT now: the build report's transitions list came back empty). Tour v08, review/v08_compare.jpg and
  review/lighting_compare.jpg looked at.
- No process running, no lock held.
