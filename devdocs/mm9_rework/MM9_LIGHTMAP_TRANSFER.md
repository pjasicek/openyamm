# MM9 lightmap transfer (Yanmir's Fort experiment, 2026-10-31)

This experiment asks: if we put MM9's own static light on our rebuilt BLV, how close does it come to real MM9? It
copies MM9's authored DAT lightmaps onto our Cycles bake's lightmap pages for `yanmirsfort`, then compares three
things: the result, our bake and real MM9 video frames. The work ran only in a staged copy. Nothing was installed in
`output/mm9_rework/assets_dev` or `assets_dev`, and no engine, shader or converter code changed.

**Answer:** with MM9's exact static light, our renderer lands within about 10 % of the real frames in brightness and
close in colour. The gap is almost all **our bake**. On these views our bake is about 33 % *brighter* than real MM9 and
more cyan-green. It is noisy as well: its floors are Cycles speckle at about 1.8× MM9's light, clipped at 1. Runtime
terms account for at most a slight remaining blue deficit.

## MM9's lightmap resolution (Yanmir's Fort)

- The WorldInfo reads `LMGridSize 32; MaxLMSize 32; AmbientLight 35 35 40`. That is **32 LT units per texel, or 81.92
  native units**. Our bake uses 16 native units per texel, so MM9 is 5.12× coarser in each direction and has 26× fewer
  texels: **572,895 texels** against our 13.9 M (4096 × 3402).
- The map has 9,919 lightmapped polygons. Per-polygon sizes are capped at 32 × 32 by MaxLMSize, which splits larger
  polygons:

  | Measure | Value |
  | --- | --- |
  | Median size | 3 × 4 |
  | 95th percentile | 18 × 22 |
  | Polygons of 2 × 2 or smaller | 257 |
  | Polygons with a side of 32 | 339 |

- Each polygon's lightmap also carries an edge row, so the effective coverage is 554 LT² per texel (23.5 LT square).
- Only 6 visible polygons lack a lightmap: 5 ice tiles and 1 solid-ice brush. The skybox faces lack one too.
- Other maps (the WorldInfo string, or the DAT's stored default of 20 where the string has none):

  | LMGridSize (LT) | Native units per texel | Maps |
  | --- | --- | --- |
  | 64 | 164 | 1000 Terrors, Anskram Keep, Chasm of the Dead, Connecting Tunnels |
  | 32 | 82 | Beethoven, Dark Passageway, Dook's Castle, Drangheim Prison, Inventa Storca, Lich Lab, Lindisfarne Monastery, Ruined Temple, Temple of Honk, The Arena, Thjorad Mine, Yanmir's Fort |
  | 20 (default) | 51 | Bathhouse, Dragon Stadium, Dungeon of Secrets, Hall of the Gods, Klusos House, Tasar Academy, Training Hall, Verhoffin Ruins |

  The polygon sizes fit grid 20 on 98–100 % of polygons, except Dragon Stadium at 82 %, which may have per-brush grid
  sizes.

## MM9's lightmap frame (verified)

The frame comes from LithTech's source in `mm9/lithtech/`: `lightmap_planes.cpp`, `CPrePoly::FindTextureOrigin` and
`CPrePoly::CalculateTextureSize`, and `CLightMapMaker::ApplyLightsToPoly`.

1. The polygon's normal N is the right-handed cross product of its ring in LT coordinates. Ignore the DAT's
   `plane_index`: its normals do not match the polygons.
2. Pick the principal plane N faces most, and take that plane's down vector Q0. Then P = N × Q0 and Q = P × N.
3. Pull the origin back along unit P and unit Q so it covers the ring, then snap it to the LMGridSize grid.
4. Texel (x, y) sits at O + (P x + Q y)·G / |P|².
5. **The data's columns run backwards: texel x is stored in column W − 1 − x.** This matches the old importer's
   `1 - u`.

**Seam test.** Neighbouring coplanar polygons sample the same world grid points, so the correct layout must make their
values agree there. The verified layout is the only one of the 8 sign/flip choices that does, over 40 k shared grid
points:

| Layout | Mean difference (of 255) | Median |
| --- | --- | --- |
| Verified layout | 1.2 | 0 |
| The other seven | 7–18 | — |

The LithTech size formula (`ceil(max P·(p − O))` rounded up to a grid multiple, divided by the grid, + 1) reproduces
96 % of the widths.

**Unresolved: a half-texel shift.** The preprocessor's oversampling shift (−G/2) cannot be told apart from no shift: the
log-luminance correlation with our bake is 0.473 either way. I used no shift, matching the old importer. The difference
is at most 41 native units.

## Encoding conversion

**MM9 side.** Lightmaps are RGB555, expanded by bit replication (`(v << 3) | (v >> 2)`) as the hardware does, and drawn
as texture × lightmap × 1 (`MM9_RENDER_LIGHTING_RE.md`). There is no gamma ramp.

**Our side.** `fs_indoor_textured_lit.sc` computes `textureColor.rgb * clamp(lightmap + dynamic, 0, 2)`:
- Indoor textures are not sRGB.
- No tonemap is applied. `cinematic_grading` is off by default. Bloom is on in the user's settings and was on in every
  capture, equally for each column.
- The surface-material path raises both terms to 2.2 and back, so it produces the same product.

**Chosen conversion: `display`, stored value = byte / 255.** Our frame then shows exactly MM9's static product, and
nothing about this is ambiguous.

**For comparison: `linear`, stored value = (byte / 255)^2.2.** It reads MM9's bytes as display values and ours as
linear radiance. That reading is wrong for this shader, and the results confirm it: about half the brightness of the
real frames.

Values are stored as RGBM like any bake and stay at or below 1, so the shader's clamp to 2 never applies.

## Tool and staging

`level_generation/projects/mm9r_common/lightmap_transfer.py <project> --out <dir> [--encoding display|linear]
[--stage <root>] [--measure] [--no-write]`

- It keeps our bake's atlas, charts and per-face affine maps. For each texel of a chart it finds the world position on
  the chart's plane, then the DAT polygons (of any world model) that face the same way, lie in the same plane and
  contain it:
  - same facing: normal dot product above 0.998;
  - same plane: within 1.5 LT, measured at the chart's centre;
  - containment: within 4.5 LT of the polygon (about half a texel of ours).

  It takes a bilinear sample from the polygon the texel sits deepest inside, clamped to that polygon's lightmap.
- Texels in a chart's rectangle but outside its faces, including its padding, take the nearest coplanar polygon within
  24 LT. A texel inside one of our faces with no MM9 match keeps our bake.
- The header, face, sector and dependency records are copied unchanged. The per-sector actor ambient therefore stays
  our bake's, and the stale-bake audit would still see the Cycles recipe.
- Run time is 70–100 s for Yanmir's Fort.
- Staging is a hard-linked copy of the review root (`cp -al`) with only `yanmirsfort.lighting` replaced by a new file:
  - `output/mm9_rework/lightmap_transfer_stage/{display,linear}/`
  - The review root's sidecar is untouched (sha `1aa29970…`, checked after every write).
  - The game loaded the staged sidecar without a staleness warning.
- Outputs, captures, measurements and the sheet script are in `output/mm9_rework/lightmap_transfer/yanmirsfort/`.

## Coverage

- **99.70 % of the texels inside our faces were transferred** (8.40 M of 8.42 M). 99.6 % of the charts matched at
  least one polygon.
- Of the transferred texels, 95.2 % came from PhysicsBSP and 4.8 % from world models (doors, cages, the trap's floors,
  the supports).
- Kept from our bake (25 k texels):

  | Kept texels | Source |
  | --- | --- |
  | 21 k | Our shaft floor at LT −3520; MM9's is at −3584 |
  | 2.2 k | Our perception-hint faces |
  | 1 k | Slivers where our outlines overhang MM9's polygons |
  | ~0.3 k | Water |

Two earlier passes needed fixes before reaching this coverage:
- Comparing plane distances at the origin rejected slanted walls far from it, because the integer vertices tilt the
  plane by about 3–4 LT. Measuring at the chart's centre fixed it (coverage went from 94.2 % to 99.0 %).
- An edge tolerance of 0.75 LT left kept-bake texels dotted along slanted face edges. Raising it to 4.5 LT fixed that.

## Comparison

The views were captured with `SDL_AUDIODRIVER=dummy ./tools/run_game.sh --isolated lmxfer_<variant> …` and
`video.view_distance=unlimited` at 1600 × 900, from the same build and settings.

**Spots.** The real frames are YouTube video frames at 1348 × 1007, with a 4:3 HUD. The two real-shot spots
(`real1_*`, `real2_*`) are the closest poses in the same rooms, not exact matches:
- `real_1`: the great hall's pillars and door. `real1_great_hall` is pose `s1_1` of `review_tour_realcand.yml`.
- `real_2`: the icicle hall. `real2_icicle_hall` is pose `s2_2`.

The other views are poses from tour v03. Their reference column is the old ODM import (`review/v02_original`), which
draws MM9's own lightmaps in our outdoor renderer.

**Measurement.** The crop is x 20–78 %, y 5–88 %. Our frames also mask the party-portrait frame (x 39–61 %,
y 77–100 %). Luma is Rec. 601 on display values, and the RGB columns give the crop mean.

| View | Reference | Our bake | Transfer, display | Transfer, linear |
| --- | --- | --- | --- | --- |
| real1_great_hall | **68.0** (38, 73, 123) real | 97.6 (54, 106, 169) | **64.6** (38, 69, 113) | 33.7 (12, 37, 73) |
| real1_alt | 68.0 real | 93.6 (48, 102, 169) | 61.2 (37, 65, 107) | 29.8 |
| real2_icicle_hall | **82.3** (47, 85, 158) real | 102.3 (53, 114, 171) | **68.0** (40, 72, 120) | 37.5 |
| real2_alt | 82.3 real | 107.1 (61, 118, 172) | 75.7 (44, 82, 130) | 48.7 |
| **Mean of the 4 real-spot views** | **75.2** (43, 79, 140) | **100.2** (54, 110, 170) | **67.4** (39, 72, 117) | 37.4 (14, 41, 80) |
| f04_great_hall_south | 134.3 old import | 91.3 | 63.6 | 34.5 |
| f09_basement | 75.1 | 60.8 | 55.3 | 49.0 |
| f10_spiral_stair | 154.5 | 46.0 | 24.8 | 2.8 |
| f11_cages_near | 130.0 | 52.4 | 39.0 | 12.4 |
| f12_key | 138.0 | 32.3 | 28.9 | 7.7 |
| f14_teleporter | 107.7 | 51.2 | 30.0 | 7.1 |
| f16_west_cave | 141.5 | 93.7 | 70.4 | 44.1 |
| f19_throne_room | 126.8 | 105.9 | 58.7 | 28.5 |
| r05_a | 127.2 | 51.4 | 54.1 | 26.5 |
| f01_start | 129.3 | 108.8 | 80.9 | 61.4 |
| f22_torch_side | 125.5 | 104.9 | 71.9 | 42.0 |
| f23_lamp | 124.4 | 83.0 | 53.6 | 25.8 |
| **Mean of the 12 other views** | 126.2 | 73.5 | 52.6 | 28.5 |

**Reading the table:**
- **Transfer (display) versus real.** The luma is 67 against 75, and the hue matches: G/R is 1.85 against 1.84, B/R
  3.0 against 3.3. MM9's exact static light under our renderer therefore reproduces the real look. What remains is
  about 10 % less light, mostly in blue. That is within the error of a compressed video frame, and dynamic light
  (party light, spells) could add it. The runtime agent should look there, not at the colour space.
- **Our bake versus real.** Our bake is 33 % too bright and too cyan-green:

  | Source | G/R | B/R |
  | --- | --- | --- |
  | Our bake | 2.0 | 3.1 |
  | Real MM9 | 1.8 | 3.3 |

  The great hall in particular reads pale cyan against MM9's mid-blue.
- **The old import is not a ×1 reference.** It draws the same MM9 lightmaps at 1.7–2× the real frames' brightness
  (126 against 75). Any judgement made against `assets_original` captures overstates MM9's brightness.
- **Texel means hide the problem.** The whole-map texel means are close (luma 0.451 ours against 0.475 MM9). Per
  surface, they are not:
  - A great-hall floor chart is 0.34 / 0.69 / 0.99 in ours against 0.27 / 0.39 / 0.54 in MM9. That is about 1.8× in
    G and B, and blue is clipped.
  - **50 % of our texels have a clipped channel**, against 25 % of MM9's.
  - Our texel-to-neighbour roughness is 0.029 against MM9's 0.0005. The great hall, entrance, north quarters and
    caves are 20–60 % brighter per texel. The children's room and east cave are bluer.

  The visible floors carry the screen, so our frames come out bright even though the averages match.

**Sheets** (reference | our bake | transfer display | transfer linear):
- `lightmap_transfer/yanmirsfort_sheet_01.jpg`: the real-shot spots;
- `_02` to `_04`: the other twelve views;
- `yanmirsfort_floor_chart_bake_vs_mm9.png`: one floor chart, our page against the transferred page, at ×4 nearest;
- `yanmirsfort_transfer_detail.jpg`: full-resolution crops.

## Visual verdict

**Clean and faithful.**
- Smooth gradients, soft pools under the claw lamps, dark pillar bases and darker bands high on the pillars, as in
  `real_1`.
- None of our bake's blotchy speckle on the floors, ceilings and walls. That speckle comes from the 610 per-polygon
  `LIGHTDEFS` lights at 128 samples, clipped at 1. Mipless sampling turns it into the large mottling seen in every bake
  column.
- No missing coverage is visible.

**Coarse but not blocky.** At 82 native units per texel, bilinear filtering gives soft light with no crisp shadows (MM9
never had them). No texel blocks show at normal distances.

**RGB555 steps.** Faint bands are visible in slow gradients near walls, for example the lamp ceiling in
`f23_lamp` near the floor line.

**Seams.** Neighbouring MM9 polygons agree on their grid points, so seams within a surface are invisible. Hard creases
appear where two faces meet at an angle, such as a pillar base's lit and unlit sides. That is MM9's own data and also
in the real frame.

**Unverified: world-model polygons.** MM9's data makes the basement planks' tops (Planks0, up-facing) dark at about
(34, 47, 55), while their undersides are bright at about (126, 254, 254). The planks therefore read nearly black in
`f09_basement`. Either MM9 really lit them that way, or LithTech lit world models in their own transformed frame
(`m_bUsingTransform` in `ApplyLightsToPoly`) and the mapping differs for them. There is no real frame of the basement
to check, and these polygons are 4.8 % of the transfer.

## Recommendation

**Transfer MM9's own lightmaps as the static light of the MM9 dungeons**, keeping our bake only for texels with no MM9
polygon (restored or added geometry). It is the only option that is exact, noise-free and cheap. A higher-resolution
re-cook would buy sharper shadows that MM9 never had, at the cost of reimplementing and calibrating its light model.
Keep the Cycles bake for maps without a DAT (MM6–MM8, Hesper) and as the fallback.

**Effort for the 24 dungeons with bakes** (all have `output/mm9_rework/bakes/<stem>/scene.json`):

1. **Hardening, about 1 day:**
   - Resolve the world-model frame: compare a door's or the planks' transfer against the old import's mapping, or
     against LithTech's transform path.
   - Infer per-polygon grid sizes where the stored default does not fit, as on Dragon Stadium.
   - Recompute the per-sector actor ambient from the transferred texels.
   - Give the sidecar a recipe and dependency of its own (the DAT's hash and the tool's) so `stale_bakes.py` is not
     auditing a Cycles recipe.
   - Add an install path through the converter's `dungeon/lighting.py`.
2. **Per map, about 2 minutes to run plus 10–15 minutes to capture, compare and look. About 1 working day for all 24.**
   - Coverage depends on how closely each rebuild follows the DAT. Maps with restored or invented geometry keep more
     bake texels, so look for seams at those boundaries.
3. **Watch the grid-64 maps.** At 164 native units per texel, light will look very soft on 1000 Terrors, Anskram Keep,
   Chasm of the Dead and Connecting Tunnels. If that is unacceptable, the fallback there is our bake *calibrated per
   surface against the transferred texels*: the transfer is now a per-texel ground truth for calibration. A floor and
   ceiling split would fix the over-bright floors that per-zone calibration missed, and denoising or more samples
   would fix the speckle.

**What to leave:**
- **A higher-resolution re-cook**, reimplementing LithTech's `LightMapMaker` (its lights with BrightScale, shadow rays,
  no bounce) at 16 units. It would take about 3–5 days with validation against the DAT texels, and it is only worth it
  if soft MM9-resolution light is rejected visually.
- **Keeping the current bake as is.** It is 33 % too bright and visibly noisy on Yanmir's Fort.

## Hardening and recipe (2026-10-31, rollout deferred)

**Status.** The user deferred the transfer to the very end of the MM9 integration (orchestrator, 2026-10-31). The tool
is hardened and ready; **no map has a transferred sidecar installed**. The same day, the user also deferred Cycles
re-bakes to that end-of-integration lighting pass (`MM9_LIGHTING_DECISION.md`). Every map rebuilt for the invisible ramp
bottoms (see the playbook), and every map whose scene file changed, had its stale sidecar removed from the review root.
A copy is in the project's `work/lighting_stale_20261031/`, and the map renders with classic lighting until that pass.
The tool's `--cycles-only` mode carries a Cycles bake onto a rebuilt BLV by face matching. It was tried on Yanmir's
Fort: all 10,289 charted faces matched. It was not kept, because the same rebuild changed the scene (the water
texture), which the bake would hide.

### What the hardening found

- **Movable brushes (world models) use their own lightmaps in the same frame.**
  - LithTech's preprocessor lights world models in world space: `CLightMapMaker::SetupWorldModels` always sets
    `m_bUsingTransform = false` and an identity transform (`mm9/lithtech/tools/PreProcessor/LightMapMaker.cpp`).
  - Their stored values follow the ring normal as the PhysicsBSP's do. Test: the polygon's luma predicted from MM9's
    `Light` and `DirLight` objects (LithTech's quartic window, cosine, cone term, AmbientLight, unshadowed) with the ring
    normal against the reversed normal, counting which is closer to the stored lightmap:

    | Polygons | Ring normal wins | Reversed wins |
    | --- | --- | --- |
    | Yanmir's Fort PhysicsBSP (1,500 sampled) | 464 | 121 (shadowed texels) |
    | Yanmir's Fort movers | 283 | 76 |
    | Lich Lab RotatingDoors | 317 | 7 |
    | Lich Lab DestructableBrushes | 96 | 20 |

    Thin sliding doors and AI tracks come out near 50:50 (both sides predict alike), which decides nothing either way.
  - The real Yanmir frame's great-hall door reads as dark as the transfer draws it (`sheet_01.jpg`).
  - **The basement planks are MM9's own light.** Planks0 (a DestructableBrush) bridges a pit: no PhysicsBSP floor lies
    under it, only at the pit's ends at −384. The pit is lit cyan from below. The planks' undersides (126, 254, 254),
    their inner sides across the 64 LT gap and the ceiling over the gap (255 cyan) catch that light. Their tops face a
    room that no light object reaches, so they keep the AmbientLight: (33, 33, 41) against (35, 35, 40). Nothing to
    fix. `overrides.yml map: {lightmap_fallback_models: [...]}` can send a model's texels to the fallback if a map ever
    needs it; none does.
- **Per-polygon grid sizes: none.** On every map, the stored sizes fit the world grid (the DAT default 20 where the
  WorldInfo string has none) on 95–99.4 % of the polygons; Dragon Stadium is the exception at 87.5 %. The fit rule is
  LithTech's size formula plus the edge row, so 0 or +1 per axis. The misfits are slivers that fit several other grids
  at once, never one other grid. The earlier "82 % on Dragon Stadium" came from a stricter formula. Every polygon uses
  the world grid, and the report lists `fits` / `size off` per map.
- **Fallback, with no per-map factor.** Some texels of our faces have no MM9 polygon: restored holes, welds, our own
  faces, and Yanmir's shaft floor 64 LT off MM9's. They keep the Cycles bake, scaled per chart and per channel by MM9 /
  bake over the transferred texels around them:
  - the neighbourhood is 64 LT voxels within 128 LT, facing the same principal direction;
  - if that has fewer than 64 texels, any facing; then 512 LT;
  - the scale is clamped to 0.1–4.
  - Emitter charts (sky faces, lit panes) keep the bake's display value.
  - Yanmir's Fort: 36 fallback charts (31 same-facing, 5 any), scale p10/50/90 0.67 / 0.73 / 1.5. Coverage is 99.70 %
    of the core texels, as in the prototype.
  - **Not yet checked by eye** in game.
- **Actor ambient.** The sector records stay the bake's. Actors, decorations and items keep their existing lighting
  path (the renderer reads their ambient from the sector records, not from the pages).
- **Staleness.** The installed `<stem>.bake.json` becomes the transfer's recipe:
  - the tool's SHA-256, the DAT's path and SHA-256, the encoding, the parameters and the fallback models;
  - the base bake's geometry hash, its sidecar SHA-256 and its full Cycles recipe, embedded.

  The sidecar's dependencies are the BLV, its scene file, that recipe, and the base bake's textures (the fallback's
  materials, plus any texture a rebuild gave a face since the bake). So `stale_bakes.py` audits it like any bake. The
  DAT lies outside the asset tree; it is original data, and its hash is kept in the recipe.
- **Carry-over onto a rebuilt BLV.** A rebuild that only removes invisible faces leaves the bake's atlas valid. The tool
  exports the current scene (`--headless-export-indoor-bake-scene`) and matches every charted face of the bake to the
  current face with the same mover flag and vertices (the stored pose for movers). The texture is matched apart:
  Yanmir's 36 water faces changed from `WATEZWECUN` to `lqw115mm9` in a later converter. It refuses, so you must bake
  again, when the sector count changes or more than 50 drawn faces have no chart. Yanmir's Fort after the rebuild:
  10,289 of 10,289 charted faces matched, 0 drawn faces unmatched.
- **Dark rooms: an option, off by default.** `--min-light V` (or `map: {lightmap_min_light: V}`) puts a floor under
  every texel as a stand-in for a player light. MM9's `PlayerLightOn` is a grey light of radius 36 LT with no visible
  effect, so the default keeps MM9's dark rooms as dark as MM9 draws them. No dark-view count was taken: the pilot did
  not run.

### Recipe (per map, when the rollout resumes)

```sh
P=level_generation/projects/mm9r_<map>
python3 level_generation/projects/mm9r_common/lightmap_transfer.py $P --measure     # MM9's grid, polygon fit
python3 level_generation/projects/mm9r_common/lightmap_transfer.py $P              # dry run: output/mm9_rework/
                                        # lightmap_transfer/<stem>/display/, report $P/work/lightmap_transfer/
python3 level_generation/projects/mm9r_common/lightmap_transfer.py $P --install    # into the review root
                                        # (backs up first to $P/work/lighting_before_transfer/ if not there yet)
python3 tools/lighting/stale_bakes.py --assets output/mm9_rework/assets_dev --check  # must not list the map
python3 level_generation/projects/mm9r_common/lightmap_rollout.py capture <stem> transfer   # real-shot and review tours
python3 level_generation/projects/mm9r_common/lightmap_rollout.py sheet <stem>      # real | before | transfer, luma.json
python3 level_generation/projects/mm9r_common/lightmap_transfer.py $P --cycles-only --install   # revert
```

- The base is always the Cycles bake in `output/mm9_rework/bakes/<stem>/`, never the installed sidecar. After a rebake
  (`dungeon/lighting.py`), run the transfer again.
- About 75–100 s per map on Yanmir's Fort's size.
- **Still to do at the rollout:**
  - The pilot on the four maps with real screenshots, with sheets.
  - The dark-view counts.
  - Removing the per-map Cycles calibration: the profile keys `direct_scale`, `bounce_scale`, `ambient_scale`,
    `ambient_colour`, `sky_scale`, `sky_bounce_scale`, Klusos House's `max_lighting` 1.4, and `texture_lights.scale`;
    also Yanmir's invented corridor fill lights in `bake.py`. They affect only the fallback, and only at a rebake,
    because the fallback is rescaled per chart.
  - Optionally, a transfer step in `dungeon/lighting.py` after each bake. It was not added: the converter lock was
    held.
- The MM9 lights that `bake.py` files add (Dragon Stadium's and The Arena's suns, Beethoven's DirLights, Inventa
  Storca's cave lights) and the runtime-light settings in convert.py stay. These are `LIGHT_GAINS` and `ROOM_LEVELS` in
  Dark Passageway, Dungeon of Secrets and the Training Hall: they set BLV lights that actors and props use.
- **Backups** of every map's installed sidecar pair, profile, `bake.py` and `overrides.yml` are in
  `level_generation/projects/mm9r_<map>/work/lighting_before_transfer/` (`REVERT.md`). They were taken before the
  2026-10-31 rebuild, so those sidecars belong to the old BLVs.
- `output/mm9_rework/lightmap_rollout_before/` is a hard-linked snapshot of the review root from the same moment, with
  the old BLVs and bakes. The stair probes and the "before" captures run against it. Delete it when no longer needed.
- "Before" captures already taken: `review/lmroll_before_{real,review}/` in Yanmir's Fort, Klusos House, Verhoffin
  Ruins and the Dungeon of Secrets.

## Layout-only base (2026-11-05, the rollout)

The transfer no longer needs a Cycles bake. `dungeon/lighting.py <project> --layout-only [--root <review root>]` runs
`tools/lighting/bake_indoor.py --layout-only`: it exports the scene, charts and packs the receiver faces at **half MM9's
lightmap grid** (`--units-per-texel` = WorldInfo LMGridSize x 2.56 / 2: 25.6, 41 or 82 native units for grids 20, 32
and 64) and writes flat grey pages, without rendering. Faces of the scene's `terrain` textures take no chart (the
terrain draws with its materials under the daylight, never its lightmap). An existing Cycles bake is moved to
`bakes/<stem>_cycles` first. A map without a Cycles profile (cities, regions) gets a minimal one
(`bakes/<stem>_layout_profile.json`).

`lightmap_transfer.py` on such a base:
- fills MM9's texels as before; a patch with no MM9 lightmap takes the MM9 light around it (the fallback, on a flat base
  the neighbourhood's own light);
- leaves a chart without lightmap (vertex-lit, as before the transfer) when most of it lies on polygons MM9 lit per
  vertex (`DatLightmaps.unlit_fraction`: the regions' terrain, cliffs and sea; Yorwick has 1 927 lightmapped and
  25 104 vertex-lit MM9 polygons);
- recomputes the actors' per-sector ambient from the transferred texels.

Measured (layout + transfer, software-rendered machine load):

| Map | Before (Cycles bake) | Layout | Transfer | Texels | Sidecar | MM9 coverage |
| --- | --- | --- | --- | --- | --- | --- |
| Yanmir's Fort (grid 32) | 2 677 s, 13.9 M texels, 29 MB | 11 s | 36 s | 3.5 M | 6.5 MB | 98.8 % |
| Sturmford City (grid 32) | none | 13 s | 28 s | 2.4 M | - | 98.6 % |
| Yorwick (grid 64, region) | none | 11 s | 51 s (20 min before the terrain skip) | 3.5 M | 1.2 MB | 92.2 % (526 charts vertex-lit) |

Runtime: each page is one BGRA8 texture (RGBM; 4096 x 861 is 14 MB of video memory, more with mips), one extra texture
read per face pixel (the baked face program); faces batch per page.

## Daylight pages (2026-11-06)

On a map whose scene has `daylight` (cities, regions) the transfer writes a version 2 sidecar: each page plus its
daylight page (the open air's share: AmbientLight and StaticSunLight; lamps predicted from MM9's Light and DirLight
objects stay on the first page), so the streets darken at night while lamps and interiors keep their light. Rule and
runtime: [INDOOR_BAKED_LIGHTING.md](../INDOOR_BAKED_LIGHTING.md) "Daylight pages"; code `DaylightSplit` and
`split_daylight` in `lightmap_transfer.py`. Dungeons (no `daylight`) keep version 1. Every open-air map needs the
transfer rerun to get the pages (the report's `daylight_split`).
