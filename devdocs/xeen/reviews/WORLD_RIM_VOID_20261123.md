# The world rim as a void, and the world as a ship (U-12, 2026-11-23)

Agent `agent:xeen-rim`. The user's ruling U-12: "overall, the Xeen world is just a giant spaceship so like some way to
visualize that would be nice, like IMO there shouldnt be a water beyond the edges but void". This file is the plan,
the engine specification and the record of the work; it is kept current.

Status (2026-11-23, `agent:xeen-rim4`): **the engine and studio void are built** (§3, plus §6's additions); the
Reviewer's **GO WITH CHANGES** (D-109) is done on shared code and X1 (§6, third and fourth sessions); the falls seen
from the land are solved by a spillway in the hull (D-112, fourth session); MM6-MM9 show no change beyond run-to-run
noise; the other 12 rim maps can start (NEXT, at the end of §6), the falls maps with the spillway and X7 with the
notch's deckless piece still to make.

## 1. What is there now

Captures from `assets_dev` before any change: `output/xeen_rim/before/<map>/` (per rim side: `low` eye height six
cells in from the cliff looking out, `along` on the cliff top looking along the rim, `high` 2,500 over the land looking
out and down; day 13:00 and night 23:30) and `output/xeen_rim/before2/<map>/` (`mid`, 900 over the land nine cells in).
Tours: `output/xeen_rim/<label>/tours/<key>.yml`, written by `output/xeen_rim/make_tours.py`; runner
`output/xeen_rim/capture.sh`.

- **Every** outdoor map (X1–X7, D1–D6) ends on one or two sides in the rim. The land stops in a one-cell terrain cliff
  (576–2,400 high: the sketch's `cliffs` line or a rim `form: level, height: 0`), and a band of 23–24 cells to the map
  edge is sea at height 0: the sketch body `water:sky` (X1, X2) or `water:rim_sea` (the rest), commented "stands for
  the stars (gap: the game draws no void)". X6 also has `water:cove`, a level-0 pocket inside its north-west corner
  where the sand-falls pour.

  | Map | Rim sides (sketch cells, y 0 north) | Map | Rim sides |
  | --- | --- | --- | --- |
  | X1 | east, x ≥ 105 | D1 | west x < 23, south y ≥ 105 |
  | X2 | south, y ≥ 105 | D2 | south, y ≥ 105 |
  | X3 | south, y ≥ 105 | D3 | east x ≥ 104, south y ≥ 104 |
  | X4 | north, y < 23 | D4 | north y < 24, east x ≥ 104 |
  | X5 | west x < 23, south y ≥ 105 | D5 | north, y < 24 |
  | X6 | north y < 24, west x < 24 (+ the cove 24–33 × 84–92) | D6 | north y < 24, west x < 24 |
  | X7 | north y < 24 (a notch to y 29 at x 68–79, the lava cove), east x ≥ 104 | | |

- The engine continues that sea to the horizon (`OutdoorDistantSea`, three border cells per side). By day it reads as
  an ordinary grey-blue coast (`before/x1/02-x1-east-along-day.png`, `before/x1/03-x1-east-high-day.png`,
  `before/x6/08-x6-west-along-day.png`); at night as dark grey fog with no stars below the horizon
  (`before/x1/06-x1-east-high-night.png`, `before/d3/10-d3-south-low-night.png`). Darkside's amber haze greys the whole
  view out over the rim (`before/d1/09-d1-west-high-day.png`, `before2/d1/03-d1-west-mid-day.png`).
- The sky: Cloudside maps use the shipped presets (themes `swamp`, `arid`, `frozen`, `ashen` by map), Darkside the
  Xeen presets `xeen_darkside_*`; every one is `below_horizon: fog` (the default). D3 and D4 have `xeen_bright_rim`
  (`rim_glow`, `below_deg: 1.5`).
- The minimap and journal map are prebuilt PNGs (`assets_dev/worlds/xeen/icons_x2/xeen_<key>.png`, rendered in Blender
  by `output/studio_cal/x1/present/{prepare,render,finish}_minimap.py`): the band is blue sea.
- Collision: the party can step off the cliff into the band; the map's travel bounds (±23,143, `MapStats.cpp`) stop it
  about four cells past the cliff. D-102 (the wild agent, this morning): every rim map has a timer event
  (`level_generation/projects/xeen/common/wild.py` `rim_fall`, `Xeen.rimFall` in `xeen_common.lua`) that lifts a party
  below z 320 in or within 1,024 of the rim sea back over the nearest return point on the rim top; it falls 850 (the
  engine's fall damage). Scenarios `tests/scenarios/xeen/rim_fall.yml`, `rim_fall_pit.yml`.
- Things at the rim (`output/xeen_rim/rim_sites.py 3`): rim waterfalls with a foot pool at 0 (X1 `rim_falls`, D1
  `rim_falls`, D2 `sprite_falls`, D3 `wrath_falls`, D4 `octopod_falls`); sand-falls (X6, decoration `xeen_sandfall`);
  lava falls (X7 cove, D6; `xeen_lavafall`); X2's rim boulders; X5's Edge Watch; D5's Parabolic Barrier frames and
  curtain reaching the north rim; reflector obelisks (X1, X5, X6, X7); cairns, stakes, a bench, chests near the edge.

## 2. What the engine already supports (code survey)

- **No designed terrain hole.** A tile whose texture name is empty or `pending` is skipped by accident
  (`OutdoorTerrainMaterials.cpp` `createMesh` `if (!tile.valid) continue;`, `createCellTextures` alpha 0,
  `outdoor_terrain_materials.sh` discard). Nothing else (water, sea, grass, minimap, movement) knows about it; not
  usable as a feature.
- `noTerrain` hides the whole terrain only.
- `below_horizon: sky` (a preset field; themes cannot set it) draws a **mirror image** of the sky below the horizon:
  blue with mirrored clouds and a mirrored sun by day, stars only at night. A world may add presets, themes, aliases
  and `maps:` in its own `rendering/sky/sky.yml` (`composeSkyLibraryYaml`), so Xeen's sky data is live (the file's
  header comment saying otherwise is stale).
- `rim_glow` already shows `below_deg` under the horizon "over the void".
- Fog: every outdoor shader fades toward `skyFogDisplayColor()` (`game/shaders/sky_common.sh`), the horizon colour or,
  below the horizon on a sea side, the distant sea. With no sea and no void it would fade rim geometry into the bright
  horizon haze.
- Movement: the terrain floor holds the party everywhere (lowest terrain z is 0); no kill plane. Void cells that keep
  their height 0 hold the party until the D-102 timer lifts it.

So the void needs a small engine change, driven by map data only.

## 3. Engine and studio specification (for the build owner)

Rule for all of it: a map without a `terrain.void` block behaves and costs exactly as today. MM6–MM9 maps have none.

### 3.1 Scene data (game)

- `game/maps/OutdoorSceneYml.{h,cpp}`: optional `terrain.void`: a list of cell rectangles `[x0, y0, x1, y1]`
  (inclusive, cells 0–127 indexed like the ODM `tile_map`/`attribute_map`, y 0 the north row). Parsed into
  `OutdoorSceneData::terrainVoidRects`; absent = empty; a rectangle outside 0–127 or reversed is a load error.
- `game/outdoor/OutdoorMapData.h`: `std::vector<uint8_t> voidCells` (empty, or 128 × 128, 1 = void), filled in
  `buildOutdoorMapStateFromScene` (`MapAssetLoader.cpp` ~4630) from the rectangles. Helper
  `bool isOutdoorVoidCell(const OutdoorMapData &, int cellX, int cellY)` beside the water helpers.

### 3.2 Not drawn

- `OutdoorTerrainMaterials.cpp`: `createMesh` skips void cells as it skips `!tile.valid` (~729);
  `createCellTextures` writes alpha 0 for them (~950), so the shader's existing discard covers any shared vertex.
- `OutdoorRenderer.cpp`: `buildTerrainLiquidVertices` (~2325) emits no water quad for a void cell; the shore planes and
  seabed built in `createMesh` (~808–929) skip void cells.
- Grass and ground decorations: `buildOutdoorMeadowField` (`OutdoorMeadow.cpp` ~135) and `scatterTerrainDecorations`
  (`TerrainDecorationData.cpp` ~837) place nothing on a void cell.
- The terrain's far grass colour and any per-cell bake read void cells as transparent (no colour); the outdoor
  lighting bake (`tools/lighting/bake_outdoor.py`) needs no change (it bakes what the game draws), check once.

### 3.3 Distant sea and the void past the edge

- `OutdoorDistantSea` (`game/outdoor/OutdoorDistantSea.{h,cpp}`): void cells count neither as water nor land in the
  side shares; add `std::array<float, 4> voidWeights` per side, the share of void cells in the three border cells,
  through the same smoothstep (0.4 → 0.8). A side with void gets sea weight 0. Pass `voidCells` in (signature gains a
  `const std::vector<uint8_t> &voidCells`).
- A 128 × 128 R8 **void mask texture** (1 = void) is created at map load only when `voidCells` is not empty; the sky
  pass binds it as `s_skyVoid` (a 1 × 1 zero texture otherwise).

### 3.4 The sky below the horizon (Enhanced sky; `fs_sky.sc`, `sky_common.sh`, `SkyRenderer`, `SkyPresets`)

- New uniform `u_skyVoid[3]` (`SkyRenderer.cpp` beside `u_skyRim`):
  - `[0]` void weights past the west, east, south, north edges (`voidWeights`);
  - `[1]` rgb: the space colour (linear), w: the star brightness below the horizon;
  - `[2]` x: the air limb's depth in radians, y: the void floor's z (0: the void cells' terrain height), z: 1 when the
    map has void (0 skips every void branch), w: unused.
  All zero on a map without void; set every frame like the other sky uniforms.
- `sky_common.sh`:
  - `float skyVoidWeight(vec3 direction)`: for a ray below the horizon, where it meets z = `u_skyVoid[2].y` from the
    camera: inside the map square, `texture2D(s_skyVoid, uv)` (linear filtering gives a soft edge); outside, the exit
    side's weight from `u_skyVoid[0]`, blended across corners exactly as `skySeaWeight`. Returns 0 when
    `u_skyVoid[2].z < 0.5`. (Only the sky pass samples the mask; `skyFogDisplayColor` uses the side weights alone, see
    below, so the many outdoor shaders gain no texture fetch.)
  - `vec3 skyVoidDisplay(vec3 direction, vec3 horizonDisplay)`: the space colour `u_skyVoid[1].rgb`, with the air limb:
    from the horizon down to `u_skyVoid[2].x` below it the colour runs from `horizonDisplay` into space
    (`smoothstep`), so the atmosphere's edge glows over the void.
- `fs_sky.sc`: in the early below-horizon exit (~253) and in the final below-horizon blend (~370), where
  `skyVoidWeight > 0` the colour is `mix(belowHorizonFog(...), skyVoidDisplay(...) + stars, weight)`; the stars below
  are `starField(vec3(-direction.y, direction.x, -direction.z)) * u_skyVoid[1].w` (turned a quarter round so they do not
  mirror the sky's), **shown by day and night** (D-rim Q1: space below a blue noon sky). The rim glow keeps adding on
  top (already below the horizon). The mirrored `below_horizon: sky` path is unchanged.
- `skyFogDisplayColor` (`sky_common.sh` ~147): below the horizon (`toFragment.z < 0`) the side weight at the exit
  (`u_skyVoid[0]`, as `skySeaWeight`) mixes the colour toward `skyVoidDisplay(normalize(toFragment), color)`, so the
  hull, the cliff and the far rim fade into the dark void instead of into a pale haze band. Gated by `u_skyVoid[2].z`.
- Classic sky style: the void pixels show the clear (flat fog) colour; no change there.
- `SkyPresets`: preset key `void` (optional block, inherited like `stars`): `color` (linear rgb, default
  `[0.004, 0.006, 0.016]`), `stars` (brightness below the horizon, default 0.9), `limb_deg` (default 3). Themes may set
  `void` too (`applyTheme`), so Cloudside maps keep their shipped presets and get the block from a Xeen theme; a theme
  `void` block overrides the preset's. Unknown keys rejected as now. Xeen writes the values (rim agent).

### 3.5 Movement (none now)

Void cells keep the terrain floor at their height (0); nothing in movement changes. The D-102 timer lifts a party
standing there within a second (D-rim Q3). A true fall (no floor over void cells, a kill plane) is not part of this
change.

### 3.6 Map Studio (`openyamm-studio/`)

- `schema/sketch.schema.json`: top-level `void`: a list of `{id, polygon, notes}` (cells, as `water.bodies` polygons).
- Lowering (`core/OutdoorLowering.cpp`, beside `readWater`/`markWaterCells`): every node inside or on a void polygon
  is set to height 0 (as the rim sea's level today) and is dry; a cell whose four corners are inside is a void cell;
  the ground tile is laid as on dry land (the cliff's rock; it is never drawn). Water bodies may not overlap a void.
- Build/install: `<stem>.scene.yml` gains `terrain.void` (the void cells merged into row runs, then runs of equal span
  stacked into rectangles; a few rectangles per map).
- `oymap export` writes the void rectangles under `terrain` (the rim kit and checks read them).
- Audit: an actor, encounter, chest, item or building on a void cell is an error; decorations and waterfalls may stand
  there (the hull skirt and the falls hang from the edge).
- Waterfalls whose foot is below 0 already build (`foot` is not bounded; `pool: 0` builds no foot water); nothing to
  change, check one.

### 3.7 Impact and tests

- MM6–MM9: no `terrain.void`, so no mask, `u_skyVoid` zero, one uniform branch per sky/fog evaluation. Check the sky
  review matrix (`tools/sky/sky_review.py capture` before/after, `compare`) on one map each of MM6, MM7, MM8, MM9, and
  `tools/xeen/regressions.sh`.
- Unit tests: `terrain.void` parse (rectangles, errors), `measureOutdoorDistantSea` with a void side (sea 0, void 1),
  the void-cell helper.
- Xeen: the rebuilt maps' captures (`output/xeen_rim/after/`).

## 4. The chosen look (decider, 2026-11-23; rows for DECISIONS under DECIDE in the rim agent's report)

| Q | Decision |
| --- | --- |
| 1 Void by day | Space: a dark starfield below the horizon by day and night, a thin bright air limb fading from the horizon haze into black over a few degrees; fog on void sides fades toward that dark |
| 2 The ship | A hull skirt under every rim cliff: Ancient plating (`xahull`; burnt `xahullbn` near D6's crash sites), girder ribs and a seam, with slow-pulsing running-light ports set into it; one procedural model and a shared placement kit, no shadows, corner pieces. **No beacons on open meadow** (only where Ancient work already stands); the hull's underside or engines far below deferred |
| 3 Over the edge | D-102's rescue kept, reworded: "You fall into the void between the stars... and wake on the rim." No death, no engine fall |
| 4 Rim falls | Water, sand and lava pour over the edge in front of the skirt and fray into the void; every foot pool removed |
| 5 X6's cove | Void: a notch in the world's edge lined by the skirt, the sand falling into space (D-31/D-35's view) |
| 6 Rim glow | D3 and D4 only, extended below the horizon over the void (the bright face lies beyond the edge); none elsewhere |
| 7 Sky maps, planes | X8, X9, D7 and P1–P4 unchanged |
| 8 Minimap | Void cells near-black with a sparse fixed star speckle; the rim line clear |

Least sure: Q1 (stars below a noon sky is stylised; a data switch back to the mirrored sky), Q3 (the user may want
death, as the originals), Q5 (depends on clean corner pieces), Q2's "no meadow beacons" (taste).

## 5. Building it

- **Hull skirt** (`level_generation/decorations/xeen_hull_claude/`): procedural GLB, origin at the top of the edge,
  hanging down; decoration rows in `worlds/xeen/models/decoration_data.txt` (4059+), bindings in
  `worlds/xeen/models/decorations.yml`.
- **Rim kit** (`level_generation/projects/xeen/common/rim.py`): from each sketch's rim sea (later its `void`), turns the
  rim sea into a `void` polygon (once the studio reads it), drops rim foot pools, and places the hull segments, corner
  pieces and falls' spills along the edge. Every outdoor `gen.py` calls it through `wild.apply`.
- **Minimap** (`tools/xeen/void_minimap.py`): repaints the void cells of an installed minimap.
- **Rim fall**: `Xeen.rimFall` line reworded; `wild.py` reads void polygons as well as rim seas.
- **Sky**: a `void` block on the Xeen presets and a Xeen theme per Cloudside rim map; D3/D4's `rim_glow` deeper below
  the horizon.
- **WORLD_DESIGN** §4's rim paragraph ("death trigger", "no new engine work") is out of date: A3's (request).

## 6. Results

### 2026-11-23, first session (no C++)

- **Hull** built and installed (`level_generation/decorations/xeen_hull_claude/`; S.md Log). A plain vertical skirt
  under the edge cannot be seen from the land (it faces away from anyone standing inland of it), so the hull is a
  ship's side seen end-on: a coping on the edge, a **deck flaring out 1,800 and down 1,000** (29 degrees: seen from the
  cliff top and from the air) with girder ribs and pulsing running lights near its lip, the lip, and the underside back
  under the land to -2,700. Pieces: `xeen_hull4` (2,048), `xeen_hull1` (512), `xeen_hullc` (a quarter turn for land
  corners), `*bn` burnt for D6. Rows 4059–4064. Review renders `level_generation/decorations/xeen_hull_claude/review/`
  (`from_void.png`, `corner_from_land.png`). In game: a test build of X2 with the hull (`XEEN_RIM_HULL=1`) built
  through the studio unchanged (decorations at z 0, facing 180 on the edge line), loaded and drew correctly
  (`output/xeen_rim/hulltest/01-x2-out-back.png`: the coping along the cliff foot; the deck under the sea until the
  void is in).
- **Rim kit** `level_generation/projects/xeen/common/rim.py`, run from `wild.apply` by every outdoor gen.py. Pieces per
  map (`output/xeen_rim/try_rim.py`): X1 30, X2 32, X3 32, X4 32, X5 55 (1 corner), X6 55 (2 corners, the cove a
  notch), X7 55 (3 corners: the lava cove's mouth and the north-east), D1 53, D2 31, D3 51, D4 51, D5 32, D6 49 (1 in 3
  burnt). Gated: changes nothing until the studio's schema lists `void`.
- **Minimap**: `tools/xeen/void_minimap.py` (tests in `output/xeen_rim/minimap/`, e.g. `x6_compare.png`); installed
  per map at its void rebuild.
- **Rim fall**: the line reworded; `wild.rim_seas` reads `void:*` polygons too, so the D-102 rescue and
  `check_wild.py` follow the void unchanged.
- **Sky data waiting for the engine**: the `void` block is optional (engine defaults); once `SkyPresets` accepts it,
  `level_generation/xeen_art/sky/make_sky.py` adds it to the Darkside presets if the defaults read wrong, and raises
  `xeen_bright_rim`'s `below_deg` from 1.5 to about 10 (D3/D4's glow rising from below the rim). Not written now: the
  loader rejects unknown keys and would disable the world's sky file.

### 2026-11-23, second session (`agent:xeen-rim2`: engine, studio, sky data, X1 pilot)

**Engine** (§3.1–3.5 as specified; details and files in `lanes/A1.md`'s Log): scene `terrain.void` →
`OutdoorMapData::voidCells`, `isOutdoorVoidCell`; void cells draw no terrain, terrain water, grass, plants or stones;
`OutdoorDistantSea::voidWeights` (a void side has no sea); `SkyVoidLook` (`void: {color, stars, limb_deg}` on presets
and themes); `u_skyFog` 40 → 42 vectors (`[40]` void sides, `[41]` space colour and limb); the sky pass's `u_skyVoid`
and the R8 mask `s_skyVoid` (made only on maps with void); `fs_sky.sc` `applyVoid` (space, a quarter-turned star field
with a fainter milky-way band than the sky's, by day and night, the limb, the rim glow on top); `skyFogDisplayColor`
fades below-horizon fragments toward a void side into space. Added after the first X1 look: **geometry under the
void's floor fades into space with its depth** (`sky_common.sh` `skyVoidDepthFog`: from 200 under 0 to full at 2,600;
every view of a fragment under 0 on a void map takes the space colour), so the hull's underside and the falls' sheets
do not end in a hard edge in space. Without `terrain.void` everything packs zeros: one uniform branch per fog
evaluation. Docs: `level_generation/lighting/SKY_RENDERING.md` ("The void past the world's edge").

**Studio** (§3.6): sketch `void` (schema, web keyed list); lowering `readVoid`/`applyVoid` (nodes inside or on a
polygon at 0, dry; void cells = four corners in; water in a void is an issue); `terrain.void` rectangles in the scene
(`outdoorVoidRectangles`); `oymap export` writes `terrain.void` from the scene beside the map; audit `void.occupied`
(actors, items, encounters, models other than falls over void cells). `oymap_tests` 517/517.

**Rim kit fixes** (`level_generation/projects/xeen/common/rim.py`): `turn_of` gave counter-clockwise turns (the
facing's convention) and 270 for east, which the schema refuses (-180..180); a studio turn is clockwise (east 90),
so east and west hull pieces hung the wrong way round (under the land); the X2 south test hid it (180 either way).
Falls over the void: `foot` -2,400 (the sheet pours past the hull's deck toward its underside and fades with depth;
`pool: 0` as before), a lip end inside the void pulled back to the land's edge. Decorations left in the void from the
sea (X1's four rocks in the surf) are dropped, except the hull, sand/lava falls and sounds; the kit's notes name each.

**Sky data** (`level_generation/xeen_art/sky/make_sky.py`): `void` block on the three Darkside stage presets (the
defaults' values: Cloudside maps get the engine defaults); `xeen_bright_rim` `below_deg` 1.5 → 10 (the bright face's
glow rising from below the rim over the void, D3/D4). `sky.yml` regenerated only after both build trees accept the key.

**X1 pilot** (lock `xeen_x1.lock`; scripts `output/xeen_rim2/x1_build.sh`, `x1_install.sh`): `void:sky` x 105-128 →
`terrain.void: [[105, 0, 127, 127]]`; 30 hull pieces; `rim_falls` foot -2,400. Audit 0 errors, town fit 0, walls 0,
doors 0, D-85 0, empty zones pass; `check_faces.py` X1: open_edge 0, back_to_back 5 (the culvert and the Witch
Tower door: the town's, not the tent or the ruins: pins p8, p11 fixed by the studio's F30/F31 in this rebuild).

Pictures (after, `output/xeen_rim/after/x1/`, compare `output/xeen_rim/before/x1/`; extra poses
`output/xeen_rim2/after_x1_extra/`):
- `output/xeen_rim/after/x1/03-x1-east-high-day.png`: noon, 2,500 over the rim: space and stars below, the hull's
  deck plating with its running lights along the edge.
- `output/xeen_rim2/after_x1_extra/03-x1-hull-side-day.png` and `06-...-night.png`: along the rim from the cliff top:
  the land ends in the hull's coping and space; at night the running lights.
- `output/xeen_rim/after/x1/01-x1-east-low-day.png`: eye height, noon: space and stars past the rim under the blue
  sky; the minimap's void (`assets_dev/worlds/xeen/icons_x2/xeen_x1.png`).
- `output/xeen_rim/after/x1/02-x1-east-along-day.png`: eye height at the creek's mouth.

Installed into `assets_dev` with its bake (12:42), terrain weights, the minimap re-rendered and the void painted
(`output/studio_cal/x1/present/prepare_minimap.py` now gives the Magic Mirror's engine-drawn `xmirror` a grey
stand-in: it stopped the render). Checks after install: audit 0 errors, check_exits, door_check, town_fit, wall_check,
check_wild (X1 clean), house signs, actor heights, key NPCs, `stale_bakes --check` 0. Tests: X1 walk and hostility
playtests, `rim_fall`, `rim_fall_pit`, `x1_bridge_walkers`, `x1_start_nothing_in_reach`; story 01-13; side quests
q-c1, q-c20, q-c21, q-c22, x1-tam, obelisks_cloudside, x8-sky: all pass. Story 03 needed no change (A3.md's Log).
`tools/xeen/regressions.sh`: 48 pass, one unit case fails as before (the staged Hesper missiles, another session's
staging). MM6-MM8 sky matrix (`tools/sky/sky_review.py`, 96 shots): MM7/MM8 unchanged; MM6 before/after on the same
`build/` tree max mean-abs 0.54 against 0.40 run-to-run (output/sky_review/rim2_before, rim2_before2,
rim2_after_build).

Seen and left (for the user or a later pass): the night void is a little lighter than by day (39,43,54 against
24,28,40: the night's haze over it, as the sea had); in the baked install Pitchfork Falls' sheet over the void does
not show from the cliff top (`output/xeen_rim2/after_x1_extra/02-x1-falls-front-day.png`: the creek ends at its
rocks; in the unbaked private root the sheet drew as a long strip into the void): to look at (the sheet's water faces
reach -2,400; the water renderer's or the bake's handling of faces under 0); the hull reads as plating from the air
and as a teal coping from the land, its deck mostly under the cliff's edge from eye height.

### 2026-11-23, third session (`agent:xeen-rim3`: D-109's ten changes on shared code and X1)

Scripts and captures in `output/xeen_rim3/` (`x1_build.sh`, `x1_install.sh`, `final_chain.sh`, `x1_tour.py`,
`cap.sh`; tours `tour_*.yml`).

1. **X1's south rim.** `x1/gen.py`: void L `[[105,0],[128,0],[128,128],[0,128],[0,105],[105,105]]`, north and west
   sides split at 105 (ridge, then `level 0`), south `level 0`, the cliff line carried west along y 104 (`RIM_Y`), calm
   land near the south rim (`roll`), the dead forest, wild fill and soil patches end at y 103; the wrecked camp and the
   cairn moved to (66, 100.5) and (92.5, 101.4); `bog_bones` to (95, 102.4); the grass zone to the map's edges. Nothing of
   the story stood in the band (no entrance, POI, quest thing or test pose; XD-04 and the dead forest stay). Kit: 53
   hull pieces, a corner piece `xeen_hullc` at (104.98, 104.98) turn 135; rescue 22 return points, 11 along y 101.
   The return points are read from the land: `wild.py` `XEEN_WILD_MAPS=<build folder>` reads a scratch build's terrain,
   so `x1_build.sh` generates twice (land, then return points on it).
2. **The hull on the land's edge.** Studio `OutdoorLowering::applyVoid`: a node *on* a void outline keeps the land's
   height (the highest land neighbour), only nodes inside lie at 0, so the land runs level to its edge and the drop lies
   in the first void cell, never drawn: no cliff face between grass and metal. Kit `rim.py` `INTO = -0.02`: pieces
   stand on the land at its height. Hull model (`build_hull.py`, installed with `tools/install_model.py`, winding 0):
   a kerb 150 over the grass with pulsing running lights on its inland face, the face running 400 into the ground;
   bindings 2,850 / 2,710. Studio test updated (`oymap_tests` 517/517). A ground zone must cover the void too, or the
   land's last corners are dirt (X1's grass now runs to the map's edges): **every map agent checks this**.
3. **Void to the horizon.** `fs_sky.sc` `skyVoidWeight`: past the terrain square the ray samples the mask at its exit
   point (border texel), so the void runs on wherever the edge is void and stops nowhere else.
4. **Night and haze.** The void is applied after mist (both sky branches); its visibility is no longer `1 - fogAmount`
   but `SkyFrameState::voidVisibility` (1 up to haze 0.4, fading only in thicker fog weather and fog cover; side weights
   premultiplied on the CPU, `u_skyVoid.w` for the mask); its stars are point stars of fixed brightness and density
   (no painted band; the night preset's band and brightness had lifted the night void to 44 against 24 by day). Measured
   (X1, 2,500 over the east rim, clear weather): day and night void identical (mean 24, 28, 40).
5. **Pitchfork Falls.** Cause of the missing sheet: not the bake (unbaked and baked roots alike) and not the water
   renderer dropping faces under 0; the lip stood on the land's last node row (x 104) and its sheet hung inside the
   land's last cell, under that cell's terrain. Now: the kit puts a void fall's lip on the land's edge, `edge: true`,
   lean 900 (`VOID_FALL_LEAN`); studio waterfall key `edge` (schema): the crags stand on the land beside the lip (feet
   in it, tops 0.8 of their size over the stream), not down the sheet. Seen from the void the sheet pours and fades with
   depth (`output/xeen_rim3/cap_falls/01-void-side.png`). **Open:** from the land behind the lip the sheet still does not
   show (`cap_falls2/`); tried without effect: a land-facing copy of the sheet face, resetting the clip plane before the
   main water draw (both reverted). Next: a frame capture of `falls-front` (RenderDoc) in the water pass; sand and lava
   falls (decorations) are not yet moved to the edge by the kit.
6. **Nothing in the void.** Studio scatter places nothing on void cells (`OutdoorPlaces` `free`); audit `void.occupied`
   is an error for any decoration over the void but `xeen_hull*`, `xeen_sandfall`, `xeen_lavafall` (sounds are no
   decorations). X1 audit 0 errors.
7. **Minimap mirror.** `output/studio_cal/x1/present/prepare_minimap.py`: the working mirrors' engine-drawn `xmirror`
   is painted with the mirrors' glass art `xkmirror`; a texture without art now stops the render (no grey stand-in).
8. **MM6-MM9 sky check:** started (`output/xeen_rim3/sky_check.sh`: baseline `build/` against `build-xeen`, targets
   mm6, mm7, mm8, mm9-thjorgard, and MM6 twice on the candidate for run-to-run noise; results
   `output/xeen_rim3/sky_compare/`, `sky_noise/`); by construction maps without void draw as before (the void's
   weight is 0, the mist and void reordering is a no-op there, the sky's own stars keep the preset's brightness).
9. **One fall per trip.** Engine: a landing on a void cell takes no fall damage. `Xeen.rimFall` (xeen_common.lua):
   a party over the void is rescued at any height (the first void cell's floor, never drawn, slopes from the land's
   height, and held a party in mid-air at 477); within the margin only below 320 as before. `rim_fall.yml` checks it
   (Hilda 40 HP, off the south rim: 21 left, one fall of 850); `rim_fall.yml` and `rim_fall_pit.yml` poses moved to the
   void beside the falls (the pit is the void now). Both pass.
10. **X1 installed** 13:55 with its bake, terrain weights, the minimap re-rendered (real mirror art) and the void
   painted. Checks: audit 0 errors (private root and assets_dev), town fit 0, walls 0, doors 0, D-85, empty zones,
   props, check_wild clean, check_exits 0, house signs 0, key NPCs, actor heights, `stale_bakes --check` 0. Tests:
   walk and hostility playtests, `rim_fall`, `rim_fall_pit`, `x1_bridge_walkers`, `x1_start_nothing_in_reach`; story
   01-13 and side quests q-c1, q-c20, q-c21, q-c22, x1-tam, obelisks_cloudside, x8-sky, normal and `--reload`: all
   pass. Captures (final install, clear weather): `output/xeen_rim3/final/` (day 01-13, night 14-26: east and south
   low/along/high, falls front/side/from the void, the signature view (76, 45) to (104, 47) (the pyramid knoll hides the
   rim from there), the south-east corner low and high, the hull from the void) and `final/x1_minimap.png`.
   Not done: D3 private test build (amber haze, rim glow, a waterfall), X6/X7 notch corners, `build/` rebuild and
   `tools/xeen/regressions.sh` (next session).

### 2026-11-23, fourth session (`agent:xeen-rim4`: sky check, falls from the land, D3, notches)

Scratch and scripts: `output/xeen_rim4/` (probe tours `probe*.yml`, `x1_build.sh`, `x1_install.sh`, `x1_chain.sh`,
`sky_check2.sh`, tours `d3_tour.yml`, `x6_cap.yml`, `x7_cap.yml`).

1. **MM6-MM9 sky check: no change beyond run-to-run noise.** `build/` (rim2's void) against `build-xeen` (D-109), 32
   shots each of MM6, MM7, MM8 (`output/xeen_rim3/sky_compare.log`), the candidate captured twice for noise (MM6
   `output/xeen_rim3/sky_noise.log`, MM7/MM8 `output/xeen_rim4/sky_noise78_compare.log`). Largest before/after
   differences: MM6 0.28 (noise up to 0.39), MM7 0.64 on `26-0900-storm-up` (noise up to 0.75; the storm and overcast
   "up" shots differ only in drifting cloud detail: `output/xeen_rim4/sky_storm_cmp.png`, before, after, after again,
   difference x8), MM8 0.34 on `24-2045-overcast-up` (cloud drift). **MM9**: the tool's target pointed at
   `thjorgard.odm`, which no longer exists (the MM9 rework made the regions BLV maps with terrain and the outdoor
   sky); `tools/sky/sky_review.py` now captures `thjorgard.blv` over its start point: before/after at most 0.027,
   noise 0.031 (`output/xeen_rim4/sky_mm9_compare.log`, `sky_mm9_noise.log`). **MM6's earlier 0.54** was
   `mm6/19-2035-clear-sun.png` (the sun setting behind moving clouds; rim2's before/after-build pair), whose own
   run-to-run difference is 0.40 (rim2) and 0.39 (rim3); this time 0.24. Noise, no code path of the void.
2. **Pitchfork Falls from the land: geometry, not the renderer.** Layer toggles (`render terrain|sky|ao|deco_models|
   bmodels|shadows|grass off`, `video.water_reflections=false`; `probe1`-`probe6`) and poses round the lip: the sheet
   is drawn from every side (from under the void on the land's side its back shows, `probe4` panel 2); hiding the
   terrain shows it from the land poses (`probe6` panel 3). From any eye inland of the edge, the land's own edge (and
   the creek valley's banks, 576 against 704-928 at the edge) lies between the eye and every point below the lip; from
   just above the lip the sheet lies in the line of sight (edge-on, `probe4` panel 1); the crags filled the view from
   the banks (`land_a_sheet.png`). A steeper one-plane sheet (lean 2,400) did not show from the reference poses
   (`cap_l2400_sheet.png`). The earlier tries (bake, a land-facing copy, the clip plane) are explained by this.
   **Fix (decider: D-112 below):** the river runs down a **spillway in the hull** first. Studio: a waterfall's
   optional `chute: [out, drop]` (the water from the lip in one plane that far out and down, then the free sheet from
   the chute's end, its foot `lean` beyond it; each plane one flow, seam on the deck's lip) and a `deck` texture role
   (a spillway plate 24 under the chute, 96 wider each side, a nose at its end and an underside back under the land);
   schema and a studio test (`oymap_tests` 517/517). Kit (`rim.py`): every rim water fall gets `chute: [1900, 1050]`
   (the hull's 29-degree flare, leaping 100 past the plate), `lean: 300`, no crags, `textures.deck: xahull`
   (`xahullbn` on D6); the hull runs on in 1-cell pieces to the spillway's sides (a gap of the water's width plus the
   plate's margin, no longer 1.6 cells each side). A fall written along the edge or with its lip in the void (D3's Wrath
   Falls, `foot: 96`) is turned to pour straight out from the nearest edge point. Captures (private build):
   `output/xeen_rim4/cap_sp2/` (falls front and side, day and night, from the void): from the land the chute shows as a
   pale band running down the hull between its pieces; from the void a spillway between two hull pieces.
   Sand and lava falls (decorations) are moved onto the edge by the kit (origin a hair inside it, the designed turn
   kept while it still pours into the void; X6 and X7 notes `... on the edge at ...`); they keep the 1.6-cell gap (no
   spillway for them yet: D-112).
3. **D3 private test** (`output/xeen_rim4/d3_cap/`, day 01-06, night 07-12; not installed): the void reads as dark
   space by day and night (mean 23, 26, 39 under the amber haze, never grey), the bright face's glow runs about six
   degrees below the horizon over the void and fades into it (`08-d3-east-high-night.png`), the Wrath Falls' spillway
   (03/09 from the land, 04/10 from the void), the south-east corner (05/06, 11/12). No shader change needed. Seen for
   the D3 map agent: its minimap is still the sea; a level grey bar crosses the falls-from-void view at the deck's
   lip (Wrath Bridge's deck edge-on, to check); Wrath Falls' `line` should be set in `d3/gen.py` on the river's mouth
   (the kit put its lip at (104, 62.9); the river ends at (104, 64)).
4. **Notch corners** (private builds; `output/xeen_rim4/notch_sheet.png`, `x6_cap/`, `x7_cap/`): **X6's cove** reads:
   the south and east runs' decks meet in the inner corners as a valley, nothing pokes through, the notch stays open
   (the north wall is all sand-fall gap). **X7's lava cove** is narrowed: its slanted side walls are five cells long and
   their decks flare 1,800 into a notch ten cells wide, framing the three lava falls in a third of the opening seen from
   the void (`x7_cap/05-x7-cove-from-void.png`) and standing out as wings over the lava from the land
   (`x7_cap/02-x7-corner-e-land.png`). Per D-109: a **deckless hull piece** (the kerb and the face straight down, no
   flare) for notch walls; not made this session (S lane's `build_hull.py`, NEXT).
5. **X1 reinstalled** (lock `xeen_x1.lock`; `output/xeen_rim4/x1_chain.sh`, then `x1_chain2.sh` after the
   spillway plating's texels were fixed: `xahull` is a band (`trim_u`), so the plate's faces take one repeat across
   their short way, audit `textures.trim_tiled` 4 errors to 0). Installed 14:47 with its bake, terrain weights, the
   minimap re-rendered and its void painted. Checks: audit 0 errors (private root and assets_dev), town fit 0, walls 0,
   doors 0, D-85, empty zones, props, check_wild clean, check_exits, house signs 0, key NPCs, actor heights,
   `stale_bakes --check` 0, `build_world.py --check` 0 differ. Tests (both installs): walk and hostility playtests,
   `rim_fall`, `rim_fall_pit`, `x1_start_nothing_in_reach`, `x1_bridge_walkers` pass; story 01, 03, 05, 07, 09, 11,
   13 pass (normal; no segment goes near the falls, so no `--reload` run). Villager spots moved by two (the
   rebuild's `villagers.py --place`). Captures, final install, clear weather: `output/xeen_rim4/final/` (the same 26
   poses as rim3's; falls `07`/`08` day and `20`/`21` night from the land, `13`/`26` from the void). The spillway
   plate is solid (a BModel; the hull pieces have no collision): a party walking down the creek slides down it and
   the rescue lifts it back from over the void.
6. **Builds and regressions.** `openyamm-studio/build-xeen` (oymap, `oymap_tests` 517/517); `build/` and `build-xeen`
   (openyamm, unit and runtime tests; no game C++ change of mine, they carry other sessions' sources incl. MX's MAW
   ranged AI). `tools/xeen/regressions.sh` on `build-xeen`: 48 pass, one unit case fails as before (the staged Hesper
   missiles, another session's staging); on `build/` the same plus the runtime tests failing on a stale
   `openyamm_runtime_tests` (12:39, before the sky's `void` key): rebuilt in both trees, both pass. No MAW ranged-AI
   unit test fails.

### 2026-11-23, map agent MA (`agent:xeen-rimmap-a`: X2, X3, X4, X5)

Scripts `output/xeen_rimmap_a/` (`build.sh <m>`: generate twice, fmt, validate, build, villagers, record, walk,
checks, private root + audit, check_wild, check_faces; `install.sh <m>`: `a5_install_baked.sh` under the bake lock,
terrain weights, minimap render + `void_minimap.py`, checks from assets_dev; `tests.sh`). Per map its L4 NOTES.md.

- **X2** (installed 15:12 with its bake): `void:sky` (y >= 105), hull 32, rescue 12 return points (y 101). Carried:
  F26 quay walls `north_wall_1-4`, `south_wall_1-5` (X1's raise/height rule: 576-1072, foot 64 in the quay, top 48
  over the terrace; the north cross lanes end a cell short of the step, as their road grading had lifted the steps'
  feet to 960), F27 `farmsteads#2` faces north (downhill). The void's outline keeps the land's height, so the rim's
  last tile row counts as land: the south-east corner's empty zone grew to 12,408 / 521 tiles; one sprite marker
  moved (94, 84) to (96, 86). Checks: audit 0, town fit 0 (entries dropped from `town_fit_pending.yml`), walls,
  doors, D-85/D-87, empty zones, props, check_wild, house signs 0, stale bakes 0; check_faces only MM7's boat model
  (Nystor's ship). Tests: walk, hostility, Danulf ring, lake dragons, leash (root twice, assets_dev); story 15, 17,
  19, 23, 25, 37, 39, 79, 81, 83, 87 normal and 17, 19, 25 `--reload`; side quests q-c2, q-c3, q-c12, q-c13, q-c17,
  q-c18, q-c19, q-c23, obelisks_cloudside normal, q-c2, q-c3, q-c19 `--reload`: all pass. Captures
  `output/xeen_rimmap_a/x2/cap_install/` (baked: rim low/along/high/mid day and night, quay walls, terrace top,
  farmstead door, hull from the void day/night, far void) against `output/xeen_rim/before/x2/`. The private root's
  night shots (`cap_after/`) show black land behind the hull: the root is unbaked; baked, it reads right.

### 2026-11-23, map agent MB (`agent:xeen-rimmap-b`: X6, D6, X7; the deckless pieces; D-114)

Scripts and captures: `output/xeen_rimmap_b/` (`build.sh <key>`: generate twice, build, villagers, record, build
checks, private hard-link root, audit, walk writer; `checks.sh`, `tests.sh`, `capture.sh`, `install.sh`;
`kit_dry.py` (the kits on in-memory copies of all 13 sketches), `notch_probe.py`, `extra_tour.py`, `sheet.py`).

1. **Sand and lava falls: no spillway (decider, D-114 in MB's report).** A spillway's chute does not show from the land
   (the water captures), sand reads by its own arch, and X7's trouble was the notch's framing. Instead the 1.6-cell
   gap behind a sand or lava fall holds plain kerbless hull faces, so from the void the fall pours in front of hull,
   not the land's slab and the pieces' cut ends.
2. **New pieces** (`xeen_hull_claude/scripts/build_hull.py`, rows 4065-4068, sprites 27065-27068, winding 0):
   `xeen_hull4n`/`xeen_hull1n` (deckless: the kerb and its face straight down) and `xeen_hullf`/`xeen_hullfbn` (no
   kerb, no deck, a plain face 16 behind the edge). **Kit** (`common/rim.py`): a run shorter than 6 cells ending in an
   inner corner of the land takes the deckless pieces and no corner piece beside it (only X7's two slanted cove walls
   in the world, `notch_probe.py`); a decoration fall's gap holds faces; a piece on the map's last cell (centre 127.5,
   refused by validate: X5, D2, D6) is skipped. `common/wild.py`: `void:cove` is a rim void (X6's cove was outside
   the rescue, `check_wild` 36 `rim.pit`). `kit_dry.py` before/after: X1-X4, D1, D3-D5 identical.
3. **X6** installed 15:13: `void:rim_sea` + `void:cove`, 72 pieces, the sand-falls in front of faces
   (`output/xeen_rimmap_b/x6/cap_extra/05`, `06`, `13` from the void; `01` the D-35 signature, `02`/`03` the cove by
   day and night), 20 return points. Checks clean (audit 0, void.occupied 0, wild/faces clean, town fit 0); walk and
   hostility 2 of 2; q-c1, q-c8/q-c9 normal and `--reload`. The rim tour's day shots without a weather command show
   the void grey (65, 65, 72): the day's random weather is above `voidVisibility`'s 0.4; clear weather 24, 28, 40
   (`output/xeen_rimmap_b/x6/cap_w/`).
4. **D6**: 64 pieces (burnt mix), burnt faces behind both lava falls (`d6/cap_extra/05`, `06`, `08`); the Necropolis
   gate on its lane's middle (F28). The void stays dark under the Darkside haze (`output/xeen_rim/after/d6/`). From
   the land the lava falls show as the river's glowing lip.
5. **X7**: the lava cove opens (deckless slanted walls, faces on the back wall): from the void
   `x7/cap_extra/12-x7-cove-from-void.png` against `output/xeen_rim4/x7_cap/05`; the D-40 signature from [67, 25]
   shows the three falls whole (`x7/cap_extra/01`, `02`), so D-114's lava-preset fallback is not needed. XD-05's back
   gate pad reaches the door (F27).
6. **Seen, left (kit, every steep rim):** a 2,048 piece takes the land's height at its middle; on X7's north crags the
   pieces step and a deck looms over the slope from the rim top (`output/xeen_rim/after/x7/10-x7-north-along-day.png`).
   Proposed: 1-cell pieces where the land along a 4-cell piece varies by more than about 150.
7. **Installed** X6 15:13, D6 15:34, X7 15:38, each with its bake, terrain weights, minimap and void paint; checks on
   assets_dev clean, `stale_bakes --check` 0, `build_world.py --check` 0 differ, `quests.py` 0 errors. Side quests
   crossing the three maps, normal and `--reload`: q-c1, q-c8/q-c9, q-c14, q-c25, q-c26, q-f1, q-f2, q-d23 (both),
   q-d27 (five), obelisks_cloudside, obelisks_darkside: all pass. The main chain and promotions are held for the
   orchestrator's single run after all 12 maps (story 61-79, 85, 87, 95-98 and promotions 67, 68, 89, 99 cross them).

### 2026-11-23, map agent MC (`agent:xeen-rimmap-c`: D3, D1, D2, D4, D5)

Scripts `output/xeen_rimmap_c/` (`build.sh <key>`: generate twice, build, villagers, record, walk, D-85, town fit,
walls, doors, empty zones, private root + audit; `install.sh <key>`: A5's/A6's install with the bake, minimap render
then `void_minimap.py`, the checks on assets_dev; `tests.sh`; `tours.py` (rim sides, every rim fall front/side/void,
every hull corner, extra poses), captures `output/xeen_rimmap_c/cap/<key>_after/`, day 13:00 and night 23:30, against
`output/xeen_rim/before/<key>/`). Every map: audit 0 errors and `void.occupied` 0 in the private root and in
assets_dev, town fit 0, walls 0, doors 0, empty zones, props, check_wild clean, D-85 as before (DIS 0), walk x2 and
hostility pass; the void stays dark space under Darkside's amber haze by day and by night on all five.

- **D3** (installed 15:09): Wrath Falls on the river's mouth (`places.py`; lip (104, 64), spillway); the gorge faces
  fitted (`GORGE_FIT`: e1 and the head's slabs 128 deeper, e1-e3 24 higher; the turf's lip shows ~32 over the rock);
  minimap void painted. The grey bar over the falls from the void was terrain water quads at the river's level over
  void cells (`OutdoorTerrainMaterials.cpp` createMesh's water loop): fixed by the orchestrator, `build-xeen` rebuilt,
  recaptured gone (`cap/d3_final/05`, `11`; probe `cap/d3_probe*.jpg`: gone with `render water off`, not terrain).
  The rim glow rises over the void (`cap/d3_after/15`, `30`).
- **D1** (installed 15:33): the north gate on its road (63.5), the Queen's Gate lanes through its passage (F28),
  `dd01_outfall` a dark doorway in the gorge face (F25/D-105); Rim Falls (31, 105) down the spillway; the south-west
  corner piece at (23, 104). Story 39's gate poses moved with the gate.
- **D2**: Sprite Falls (58, 105) down the spillway; 32 pieces (no piece on the last cell, MB's kit fix).
- **D4**: Octopod Falls (104, 67) down the spillway; the glow over the void; the north-east corner (104, 24). The
  pieces beside the spillway stand at the banks' height and step on the hills (`cap/d4_after/02`, `07`, `12`), as the
  kit places them.
- **D5**: the Parabolic Barrier's end pylons on the land's edge at y 24.2, the curtain meeting the hull's kerb.
- Tests: D3's story segments 55-69 (normal, before the orchestrator took over the chains) and the 38 standalone side
  quests that cross D1-D5 (incl. obelisks_darkside, after all five installs) pass. The main chain and promotions are
  left to the orchestrator's full run (story 39's gate poses changed with D1's north gate).

- **X3** (installed 15:30 with its bake): `void:rim_sea` (y >= 105), hull 32, rescue 19 return points (y 101); no
  pending item. check_faces 0 (tents and ruins fixed by the regeneration). Checks as X2's, all 0. Tests: walk,
  hostility (root twice, assets_dev); story 19, 21, 25, 27, 29, 31, 35, 37, 81, 83, 87 normal and 27, 29
  `--reload`; side quests q-c7, q-c12, obelisks_cloudside normal, q-c7 `--reload`: all pass. Captures
  `output/xeen_rimmap_a/x3/cap_after/`.
- **X4** (installed 15:35 with its bake): `void:rim_sea` (y < 23), hull 32; the rescue has 3 return points (107, 27),
  (52, 27), (46, 27), the rest of the rim top being the Gargoyle range, unreachable on foot. Carried: `xd25_stair`
  (the kit's doorway mouth; dropped from `town_fit_pending.yml`). X4's only water fall is inland (tarn to pool): not
  a rim fall, no spillway; the F29 cut reads as before. check_faces 41, none from tents or ruins (village wall 32,
  eyrie 6, falls 2, the stair's cap 1). Tests: walk, daily, hostility; story 13, 15, 21, 23, 25, 29, 81, 83, 85, 96
  normal and 13 `--reload`; side quests q-c1, q-c3, q-c5/q-c11, q-c10, obelisks_cloudside normal, q-c5/q-c11 and
  q-c10 `--reload`: all pass. Captures `output/xeen_rimmap_a/x4/cap_after/`, `cap_look*_{before,after}/`.

- **X5** (installed 15:40 with its bake): `void:rim_sea` (west x < 23, south y >= 105), hull 54 with the corner
  piece at the south-west land corner (MB's kit fix: no one-cell piece on the last cell 127.5); rescue 17 return
  points. No pending item. Edge Watch reads with the hull behind it; with the install's terrain weights the snow runs
  to the hull (the root's rocky edge strip was the old weights). check_faces 9 (palisade rails 8, XD-10 north door
  1; tents 0). Tests: walk, hostility, Randon; side quests q-c1, q-c4, q-c6, q-c14, q-c15, q-c16, q-c18,
  obelisks_cloudside normal, q-c6 and q-c16 `--reload`: all pass. Captures `output/xeen_rimmap_a/x5/cap_install/`.
- Story segments: run for X2-X4 (above); from X5 on, by the orchestrator's order, left to its whole-chain run after
  all 12 maps (the checkpoints are shared and every install makes them STALE).
- Program checks after the four: `stale_bakes --check` 0, `build_world.py --check` 0 differ, `quests.py` exit 0,
  `towns.py --strict` no error.

### 2026-11-23, rim-weather agent (`agent:xeen-rim-weather`: the void in every weather)

Scripts and captures: `output/xeen_rim_weather/` (`make_tours.py`, `cap.sh`, `measure.py`, `mm_wet.py`,
`sky_check.sh`; captures `before/` (build-xeen) and `after/` (build-mx), `measure.txt`, sheets `x1_sheet.jpg`,
`d3_x6_sheet.jpg`, `after/<map>/contact_sheet.jpg`).

1. **Cause.** One term: `SkyFrameState::fogAmount` above 0.4 (D-109's threshold) lowered `voidVisibility`, which
   scaled the void's weight in the sky pass (`u_skyVoid.w`), so the void mixed into the below-horizon fog colour. Every
   grey case is fog distance reaching the sky through `fogAmount = 1 - strongDistance / 12288`: MMerge's sky-ladder fog
   (overcast from ladder state 3 on, rain and storm states; X6's day was ladder 3: (65, 65, 72)), snow's and ash's
   precipitation haze, and dense fog days. Overcast dimming, the rain/snow preset haze over a painted sky (capped at
   0.4) and the precipitation particles do not grey it; fog distances of 7,373 and more (`fog_small`, `fog_avg`) were
   already dark.
2. **Fix (engine, `SkyState`, `SkyRenderer`; in `fs_sky.sc` a comment only; no data change).** The sky pass's void ignores every weather:
   `voidVisibility = 1 - fogCover` (only an open sky's indoor fog cover takes it away; no Xeen map has one), and the void's
   stars are no longer dimmed by fog. Geometry fogging toward the void keeps D-109's curve as a separate
   `voidFogVisibility` (the side weights in `u_skyFog`), so in fog weather the land, the kerb and the falls still fade into
   the grey fog while the void behind them stays dark; geometry under the void floor fades into the void as before.
   Unit test "no weather greys the void ..." (`tests/SkyStateTests.cpp`).
3. **Measured** (void mean over a void-only rect of the high shot looking down past the rim; 12 weathers x day 13:00 and
   night 23:30; `measure.txt`). Before: day 62-141 grey in auto/overcast/ladder 6/rain/storm/snow/dense fog/rain+fog
   (X1 117 in ladder 6, D3 141), night 30-37. After, X1 and X6: day 24-26, 28-30, 40-42 (rain, storm and snow +1-2
   from their streaks and flakes), night 24, 28, 40 in all 12; D3 (Darkside haze): day 25-28, 29-32, 41-43, night
   25-28, 28-31, 40-42 (clear 26, 30, 41 / 28, 31, 42). Low shots from the land (spillway gap, X6 sand falls, D3 east)
   show the same dark void behind a grey-fogged kerb.
4. **MM6-MM9 unchanged.** By construction (both values reach the shaders only where `hasVoid`), and measured:
   `sky_review.py` MM6, MM7, MM8, `mm9-thjorgard` before (build-xeen) against after (build-mx), after twice for noise,
   plus `mm_wet.py` (rain, storm, snow, fog, rain in fog, day and night, horizon and high; MM9 open-sky rain, snow and
   fog levels). The first before run of MM6 differed by up to 1.49 in its cloudy shots (cloud drift: it ran beside two
   other game runs; before against a second before 1.63); a second before run against after: at most 0.59
   (`19-2035-clear-sun`, noise 0.39-0.54 in earlier sessions). MM7/MM8/MM9 within noise (after twice: up to 6.2 on
   drifting overcast clouds). Wet shots: largest 4.27 (`mm7/18-1300-rainfog-high`) against noise 3.71 and 4.09; the
   differences are rain streaks, clouds and water ripples (`mm7_rainfog_diff.jpg`). Logs `sky_compare*.log`,
   `sky_noise*.log`, `wet_compare.log`, `wet_noise.log`.
5. **Binaries.** `build-mx`, then after the story run `build-xeen` and `build/` (openyamm, unit and runtime tests).
   `tools/xeen/regressions.sh`: 48 pass in both; the unit tests fail only the staged Hesper missiles case (as before),
   and on `build/` once a mercenary-recruit case that passes 3 of 3 alone in both trees (flaky, not sky code).
   X1 from assets_dev on the new `build-xeen`, the day's weather and dense fog: void (24, 28, 40) in both
   (`output/xeen_rim_weather/confirm_sheet.jpg`).

### NEXT: the other 12 rim maps (for their map agents, once the user accepts X1)

Binaries: `build-xeen/game/openyamm` and `openyamm-studio/build-xeen/oymap` read and draw the void (and `build/`).
Every outdoor gen.py already runs the kit (`wild.apply` → `rim.apply`): regenerating a map turns its rim sea into the
void, places the hull and pours its falls into the void. Per map, one at a time under its lock, AGENT_GUIDE §5.1 in
full (X1's scripts `output/xeen_rim2/x1_build.sh` and `x1_install.sh` are the pattern: generate, fmt, validate,
build, villagers, record, gen_walk, D-85, town fit, walls, doors, empty zones, private root + audit; install with the
bake, terrain weights, the minimap render then `python3 tools/xeen/void_minimap.py <key> --install`, key NPCs, actor
heights, check_exits, props, check_wild, house signs, playtests, `rim_fall*.yml`, `stale_bakes --check`), then
captures `python3 output/xeen_rim/make_tours.py after <key>` (reads `void:` polygons too) against
`output/xeen_rim/before/<key>/`, and the story segments and side quests that cross the map (§5.6).

| Map | Rim | Carry in the same rebuild (`tools/xeen/town_fit_pending.yml`, PLAYER_FEEDBACK_20261123.md) | Look at |
| --- | --- | --- | --- |
| X2 | south | terrace walls `north_wall_1-4`, `south_wall_1-5` (`raise`/`height` as X1's), `farmsteads#2` buried door | Q-C19 Ligono's "surf" lines (A3) |
| X3 | south | none | |
| X4 | north | `xd25_stair` (kit fixed; rebuild only), its falls (F29 cut) | |
| X5 | west, south (1 corner) | none | Edge Watch at the rim |
| X6 | north, west, the cove (2 corners) | none | the cove's notch and sand-falls (decider Q5) |
| X7 | north (lava cove notch), east (3 corners) | `xd05_gate` buried door (look) | lava falls in the gaps |
| D1 | west, south | gates `wall_ne`, Castleview; `dd01_outfall` (D1 generator) | `rim_falls` |
| D2 | south | none | `sprite_falls` |
| D3 | east, south | gorge faces `gorge_face_e1-e3`, `_head_w`, `_head_e` (look) | the rim glow below the horizon |
| D4 | north, east | none | `octopod_falls`, the rim glow |
| D5 | north | none | the Parabolic Barrier reaching the rim |
| D6 | north, west | `np_gate_wall` gate | burnt hull (`*bn`), lava falls |

D-109 adds to every rebuild (pattern: `output/xeen_rim3/x1_build.sh`, which generates twice with
`XEEN_WILD_MAPS=<scratch build>` so the rescue's return points follow the new land): a ground zone covering the
void as well as the land (else the land's last corners are dirt); no scatter polygon or wild fill beyond the edge (the
studio drops it now, but its count drops too); every decoration off the void (audit `void.occupied` is an error);
sand and lava falls (X6, X7, D6) placed on the land's edge by hand until the kit moves them; check the kit's corner
pieces. Falls maps (D1, D2, D3, D4): the kit gives every rim water fall the spillway (D-112): after the build look at
the falls from the land and the void (the hull pieces beside the spillway stand at the banks' height and can hide the
chute's start from low poses); D3's Wrath Falls line in `d3/gen.py` on the river's mouth. X7: the lava cove's side
walls need the deckless hull piece first (fourth session item 4; S lane: a `xeen_hull1n`/`xeen_hull4n` pair in
`build_hull.py`, rows 4065+, and `rim.py` choosing them on runs shorter than about six cells inside a notch); X6's cove
is fine as built. Sand and lava falls stay over a gap in the hull until a spillway for them is decided (D-112).

Drop each fixed entry from `town_fit_pending.yml`. Kit notes to read on each map's gen log: `wild: void: ...`,
`... pours into the void`, `dropped ... from the void` (check each dropped decoration is a sea leftover), `hull: N`.
The Darkside themes' haze (0.14-0.28) also hazes the void like the sea (`1 - fogAmount`): if D maps' void reads grey,
give their themes a darker `void` or lower the haze's share there (a shader change: ask the build owner).
