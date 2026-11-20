# Indoor baked lighting (BLV lightmaps)

Native indoor maps (BLV) normally light their faces with the static lights baked into vertex colours (at most a few
per face, no shadows, no bounce) plus the sector ambient, and the dynamic lights (torch, spells, projectiles, effects)
from the light grid. A BLV may instead carry a **baked lighting sidecar**: lightmap pages with the static lights' direct
light and soft shadows, its bounce off the walls and the sector ambient as a floor. It is opt-in per map: a map without
one (every MM6–MM8 dungeon, Hesper's) renders exactly as before. First user: MM9's Anskram Keep
(`level_generation/projects/mm9r_anskramkeep/`, review root `output/mm9_rework/assets_dev`).

The outdoor bakes are the model ([outdoor README](../tools/lighting/baked_outdoors/README.md),
[format](../tools/lighting/baked_outdoors/FORMAT.md)); the two share the RGBM page encoding, the RLE spans, the content
hash, the dependency records and recipe, the chart packer and Cycles as the baker (`tools/lighting/bake_geometry.py`,
`game/render/lighting/BakedLightingFormat.*`).

## Bake

```sh
cmake --build build --target openyamm -j25        # the producer reads the scene from the game
blender --background --factory-startup --python-exit-code 1 --python tools/lighting/bake_indoor.py -- \
    --profile tools/lighting/baked_indoors/profiles/mm9_anskramkeep.yml --output <dir> \
    --assets output/mm9_rework/assets_dev [--samples 16] [--recompose] [--extra-lights <lights.json>]
cp <dir>/<map>.lighting <dir>/<map>.bake.json <assets>/worlds/<world>/maps/   # an assets_dev map
python3 level_generation/projects/mm9r_common/dungeon/lighting.py level_generation/projects/mm9r_<map>
                                                    # an MM9 dungeon: bake (with its extra lights), install in the review root
```

1. **Scene from the game.** `openyamm --headless-export-indoor-bake-scene <map.blv> <out.json>` loads the map as the
   game does and writes every drawn face (room, back room, texture, attributes, visibility, whether a door moves it,
   BLV plane normal, vertices in their load pose; for a door-moved face also its vertices in the BLV's stored pose,
   `stored_points`, and `mover_receiver`: whether the bake lightmaps it, `indoorMoverFaceBakeable`), the static lights exactly as the renderer lights with them
   (`buildBakedStaticLightSources`: map lights with a radius and light-emitting decorations, at their initial state)
   and each sector's ambient (`IndoorLightingRuntime::ambientFromMinAmbientLightLevel`).
2. **Charts.** Receivers are the visible faces that do not show the sky: every static face, and the door-moved faces
   that move rigidly a short way (below, "Doors and other movers"), charted in their stored pose. Coplanar faces that
   touch (same facing, a shared vertex) join one chart (`group_coplanar_faces`) while the joined rectangle stays within
   1.25 times their two rectangles: a floor or wall split at a portal or by MM9's BSP bakes without a seam, but a whole
   storey does not become one mostly empty chart. Charts use world-aligned in-plane axes (`plane_chart_basis`), texel
   centres on their bounds, and are packed first-fit (`pack_lightmap_charts(first_fit=True)`; the outdoor default
   wastes most of a page on thousands of small charts) into `page_size` pages with 2 texels of padding (and a 2-texel
   Cycles margin). The file stores, per face, the affine map from world position to page UV, so the runtime needs no
   per-vertex records and subdivided or triangulated vertices map exactly.
3. **Cycles.** Every visible face casts and bounces (a baked mover in its stored pose, the other movers in their load
   pose: doors normally closed); each face's material
   is its texture's mean linear colour (magenta key excluded), roughness 1, no specular. Each static light is a Cycles
   point light of `light_size` radius (soft shadows) whose emission follows the runtime's window with no inverse-square
   falloff: `Light Falloff.Constant * (1 - (d/r)^2)^2` (calibrated: Cycles' light-only DIFFUSE response of a constant
   falloff point light of power P is `P cos / (4 pi^2)`). So an unshadowed texel facing a light carries the runtime's
   own static light, `1.35 * alpha * colour * (1 - d^2/r^2)^2`, times its cosine. `--extra-lights` adds bake-only
   point lights of the same model (below). Two passes per page: direct, and indirect (`bounces` diffuse bounces); a
   map with `emitters` bakes two more, `sky_direct` and `sky_indirect`, with the point lights off and the emitters on
   (the lamp passes have the emitters off).
4. **Compose** (numpy, `--recompose` redoes it in seconds from the saved passes, and refuses when the BLV changed):
   `direct_scale * (direct + bounce_scale * blur(indirect)) + ambient_scale * sector ambient
   + sky_scale * (blur1(sky_direct) + sky_bounce_scale * blur(sky_indirect))`, the indirect blurred within each chart
   only (its sampling noise), clamped per channel to `max_lighting` (default and limit 4). An emitter's own faces take `display * colour` (the sky or the lit pane).
   Per sector, the mean of the bounce, sky and floor over its surfaces becomes the **actor ambient**.

Profile keys (JSON in `tools/lighting/baked_indoors/profiles/`, defaults in brackets): `world`, `map`,
`units_per_texel` (16), `page_size` (2048), `padding` (2), `samples` (128), `bounces` (3), `light_size` (24 units),
`direct_scale` (1), `bounce_scale` (1), `ambient_scale` (0.5), `blur_radius` (2), `emitters` (none), `sky_scale`
(1), `sky_bounce_scale` (`bounce_scale`), `outward_distance` (4096), `glass` (none), `max_lighting` (4),
`ambient_colour` ([1, 1, 1]), `shadowless_faces` (none); read by
`dungeon/lighting.py`: `dirlights` (false), `texture_lights` (one per brush).

**Shadowless faces (`shadowless_faces`, 2026-10-31).** BLV face indices whose bake material is transparent to shadow
rays: they are lit, bounce light and receive their own lightmap, but cast no shadow. MM9's world models (its
DestructableBrush pillars) cast none in its lightmaps, and a face a script can hide (`evt.SetFacetBit`) would otherwise
leave its shadow on the floor. Dragon Stadium's `convert.py` writes its 21 pillar levels' faces into its profile after
each build (face indices change with the BLV). Empty by default: every other profile bakes as before.

**Ambient colour (`ambient_colour`, 2026-10-31).** An RGB factor on the ambient floor (and the actor ambient of a sector
with no baked surface), default white. MM9's WorldInfo `AmbientLight` is coloured and its lightmaps show it wherever
no light reaches: Connecting Tunnels' 15/25/35 gives its unlit tunnels a blue cast (B/R 1.3-1.7), which a grey floor
cannot match; normalise the colour to luminance 1 and keep `ambient_scale` for the level.

**Ceiling (`max_lighting`, 2026-10-30).** MM9's lightmaps clip at 255, ×1 on the texture, while the bake reaches ×4 near
overlapping lights. A profile's `max_lighting` applies that ceiling, so a bright room does not force the scales down for
the whole map (Anskram Keep: direct 1.0, bounce 6, ambient 0.5 at ceiling 1, instead of compressing the range with
direct 0.48, bounce 10.5). `--recompose` retunes it. Per channel, as MM9: warm light over the ceiling goes paler.

**Translucent faces (2026-10-30).** A face the scene makes translucent ([translucent indoor
faces](INDOOR_TRANSLUCENT_FACES.md)) is a receiver like any other, charted apart from opaque faces, and in Cycles a mix
of a transparent BSDF and its tinted diffuse colour: with alpha = opacity × the texture's mean alpha it lets 1 − alpha
of the light and of every shadow ray through and scatters the rest. It is never an emitter. The profile's `glass`
(`[{textures, colour, display}]`) sets a floor for those textures' translucent charts: their lightmap is at least
`display * colour` (MM9's preprocessor lights translucent glass unshadowed from both sides, so its panes read bright;
the bake gives a pane only the light on its front); `--recompose` retunes it in seconds.
A face of a see-through liquid (`liquids.yml` `opacity` below 1, 2026-10-31) is exported the same way, with the
liquid's opacity and no tint, so its bed is lit through it; its bitmap needs an opaque alpha so that only the opacity
counts ([see-through liquids](INDOOR_TRANSLUCENT_FACES.md#see-through-liquids)).

**Sky and windows (`emitters`, 2026-10-30).** Indoor maps have no sky, so a dungeon that its original lit through
skylights and windows bakes dark there. Each emitter is `{textures, colour (linear RGB), strength, display,
outward}`: the visible faces with one of its textures are Cycles area lights of radiance `strength * colour` (in
lighting units: a texel facing a hemisphere of it gets `strength`), charted apart from other faces, drawn at
`display * colour`. `outward: true` (window panes) keeps only the panes whose back looks out of the map: the ray from
the pane's back runs `outward_distance` without hitting a face, or hits a non-outward emitter (the sky behind a
skylight's glass); a pane against a wall stays an ordinary face. The MM9 dungeons use MM9's sky faces (`skymarker`,
drawn with its Clouds1 sky) and their outward panes.

**Extra lights (`--extra-lights`, 2026-10-30).** A JSON list of `{position, radius, color, alpha}` in native units:
bake-only point lights; with `direction` (a unit vector) and `fov` (the full cone, degrees) a spot. `level_generation/projects/mm9r_common/dungeon/lighting.py` passes the MM9 lights its
converter left out of the BLV because a floor point was already under four (the runtime's limit for vertex lights and
the light grid; MM9's large fill lights): the lightmap has no such limit. They are not in the BLV, so actors and the
light grid do not see them (the sector's actor ambient does). The list is part of the recipe (`<map>.bake.json`
`extra_lights`) and saved with the passes for `--recompose`.

**Directional lights (profile `dirlights: true`, 2026-10-30).** `dungeon/lighting.py` adds MM9's `DirLight` objects
(1,189 in all) as bake-only spots: `InnerColor`, `LightRadius` × 2.56, `BrightScale` relative to the map's typical kept
light as for the capped lights. MM9's preprocessor (`tools/PreProcessor/LightMapMaker.cpp`) defines them: the forward
vector of `gr_SetupMatrixEuler`, (cos p sin y, -sin p, cos p cos y), so a pitch of 4.71 aims **up**; the same quartic
window as our lights, times a linear cone term. Cycles spots with full blend give a smoothstep of that term (equal at the
axis, half way and the edge) and, on the axis, 2 / pi of a point light's response, which `CYCLES_SPOT_FACTOR` restores
(measured). Opt-in per profile because a map's calibration moves with them; a converter's dungeon turns it on when it
next calibrates. They reach neither the runtime's lights nor the light grid.

**Anskram Keep** (`mm9_anskramkeep.yml`): one 4096 × 1625 page (6.7 M texels, about 26 MB of RGBA8 on the GPU, an
8.6 MB file), 6 569 charts for 7 921 of 8 760 faces, about 95 s of Cycles on 16 CPU threads. `direct_scale` 1.6
makes up for the cosine and shadows the vertex bake never had, `bounce_scale` 6 gives the bounce visible colour (it is
weak in these units: the keep's textures average about 0.15 albedo), `ambient_scale` 1.0 (0.85 since 2026-10-30, with
`Light6` as an extra light) keeps the native room ambient as the floor; together the 18 review views average the brightness of the native and MM9 renders (47 / 49 /
49 of 255). One page keeps every lit batch whole (352 batches against 331 unbaked; two 2048 pages split them into
535). A GLES 3.0 device guarantees only 2048-texel textures: for Android, bake with `page_size` 2048 (and 20–24 units
per texel).

**Texel density: 16 units per texel.** The party's eye is at 160 and a door 256 tall, so a 512-tall wall gets 32
texels, a light of radius 384–768 falls off over 24–48 texels, and the shadow of a 64-unit beam spans 4 texels. 8
gives sharper shadows at four times the memory (Anskram Keep: about 19 M texels); 24 or 32 is the choice for Android
if memory demands it.

**MM9 texture lights (`LIGHTDEFS`, 2026-10-30).** `dungeon/lighting.py` adds a bake-only point light per built brush
using a texture whose DTX has a `LIGHTDEFS` `center x y radius r g b` section, at the centre of its polygons with that
texture, of that colour and radius (`devdocs/mm9_rework/MM9_VISUAL_PROPERTIES.md` finding 1; the Lich Lab's teal ice
glass of the engine's pods and crown). A profile's `texture_lights: {per_polygon: true, scale, offset_lt}` adds one light
in front of each polygon instead, at `scale` of full strength: a brush centre shut in behind metal lights nothing, as
the Lich Lab's pods showed (37 lights; at full strength they flood the floor).

**MM9's own lightmaps (deferred, 2026-10-31).** `level_generation/projects/mm9r_common/lightmap_transfer.py` writes an
MM9 dungeon's sidecar from its DAT lightmaps (texel = byte / 255, the renderer's `texture x lighting` then equals MM9's
`texture x lightmap`). It uses the Cycles bake's atlas and charts, a per-chart rescaled Cycles fallback for faces MM9 has
no polygon for, and the bake's actor ambient. Its recipe, `<map>.bake.json`, embeds the base bake's recipe with the
DAT's hash, so `stale_bakes.py` audits it like any bake. `--cycles-only` carries a Cycles bake onto a rebuilt BLV by face
matching. Method, findings and the per-map recipe are in `devdocs/mm9_rework/MM9_LIGHTMAP_TRANSFER.md`. The user deferred
it, with all Cycles re-bakes, to the end of the MM9 integration: since 2026-10-31 the review root's rebuilt or
scene-changed MM9 dungeons carry no sidecar (classic lighting; copies in each project's
`work/lighting_stale_20261031/`).

**Daylight pages (version 2, 2026-11-06).** A map open to the sky (scene `daylight`: the MM9 cities and regions)
lights its lightmapped faces by the hour as the vertex-lit ones are. Before, MM9's transferred lightmaps (its
AmbientLight, StaticSunLight with shadows and lamps in one value) drew noon light at midnight: Sturmford City's streets
measured 85 at noon and 72 at midnight (centre-crop luma) while the region's vertex-lit ground went 63 to 27.
`level_generation/projects/mm9r_common/lightmap_transfer.py` now splits each texel of such a map into the open air's
share D (ambient and sun at noon) and the rest (lamps, and everything under a roof), per channel: the lamps predicted
from MM9's Light and DirLight objects as its preprocessor lights them, unshadowed (on MM9's own shaded faces this
matches the lightmap's light over the ambient at a median ratio of 1.01), and D = clamp(V - lamps, min(A, V),
min(V, A + sun x clamp(4 N.L) + open air))), A the AmbientLight and "open air" MM9's lights over the open land
(`LightRadius` 750 LT and up, which stand in for the sun on the regions; lamps reach at most 700 LT; 2026-11-07,
INDOOR_OPEN_SKY.md "Daylight", open-air lights), predicted like the lamps; before, they counted as lamps and kept the
regions' structures lit at night. So a face turned away from the sun keeps only A as daylight, a
lamp pool in shade stays a lamp pool, and a sunlit texel MM9 clipped at 255 keeps its predicted lamps at night. At run
time (`fs_indoor_textured_lit.sc` `indoorStaticLight`, `u_indoorBakedDaylight`, `indoorBakedDaylightScale`) a face of
a sector open to the sky (`v_faceInfo.z`) draws `rest + min(D, A) x ambientScale + (D - min(D, A)) x sunScale`, the
scales being the scene daylight now over at noon (the same light, night floor and sky hue as the vertex-lit faces open
to the sky); every other face, and every map without daylight, draws `rest + D` = the bake. The lightmapped faces take
no `u_indoorDaylight` term. A map whose sidecar is version 1 draws as before (one uniform test per pixel, no fetch).
Cost on such a map: a second page texture of the same size and one more fetch per lightmapped pixel. Sturmford City:
noon 85 / midnight 72 before, see the city README for after.

## Format (`<map>.lighting`, versions 1 and 2)

Little endian. Magic `OYILIT1\0` (the indoor member of the `OYMLIT1` outdoor family). Lengths, offsets, counts, page
references, finite values, dependency paths and RLE spans are validated; trailing data is rejected.

| Offset | Type | Meaning |
| --- | --- | --- |
| 0 | 8 bytes | Magic |
| 8, 12 | u32 | Version 1, header bytes 64 |
| 16 | u64 | FNV-1a 64 of the BLV bytes the bake was made from |
| 24, 28 | u32 | BLV face count, sector count |
| 32, 36 | u32 | Page count, dependency count |
| 40, 44, 48, 52, 56 | u32 | Offsets: page records (64), face records, sector records, dependencies, pixel data |
| 60 | u32 | File length |

- **Page** (16 bytes): width, height, absolute payload offset, payload bytes. Payloads are adjacent in page order and
  the last ends at the file's end. Each is the outdoor RLE of BGRM texels (`RGB * M * 4`, see the outdoor FORMAT.md),
  rows bottom-up as Cycles bakes them (UV v = 0 is the first row). Values are in the indoor renderer's lighting units
  (the multiplier on the texture colour; the shader clamps the sum to 2).
- **Face** (36 bytes, one per BLV face in face order): page u16 (`0xffff`: not lightmapped), flags u16 (bit 0:
  lightmapped, set exactly when the page is), then `uAxis` and `vAxis` (4 f32 each): `u = dot(p, uAxis.xyz) + uAxis.w`.
  For a face a door moves, `p` is the vertex in the BLV's stored pose (the vertex array as stored). Sidecars from
  before 2026-10-30 have no page on any mover face; the format and version are unchanged.
- **Version 2** (daylight pages, above): the same layout with an even page count; page records come in pairs of equal
  size, the static light (2i) then the open air's light at noon (2i+1), and a face references its pair's first
  record. Noon light is their sum. The loader keeps the pairs as `pages` and `daylightPages`.
- **Sector** (12 bytes, one per sector): actor ambient RGB in lighting units, 0–4.
- **Dependency**: path length u32, FNV-1a 64 u64, UTF-8 path rooted at `engine/` or `worlds/`. The producer records
  the BLV, its scene file, every drawn face's texture and the installed recipe (`<map>.bake.json`, which holds the
  profile, Blender version and producer hashes).

## Runtime

- **Load** (`MapAssetLoader`, BLV branch, full presentation only): `<map>.lighting` beside the map is parsed by
  `loadIndoorBakedLighting`; a bake whose geometry hash or face/sector counts differ from the loaded BLV is **stale and
  ignored** (logged: "Ignoring the baked lighting of …"), as is a corrupt one; the map then renders unbaked. A valid
  bake is shared on `IndoorMapData::bakedLighting`. Pages stay RLE-compressed on the CPU and are decoded once for
  upload.
- **Selection, once per batch build** (`IndoorRenderer::rebuildAllTexturedBatches`):
  `IndoorBakedLighting::faceLightmap` gives each face its page, or -1 (no bake, `[video] lightmaps` off, not
  lightmapped), and for a door-moved face the UV offset back to its stored pose (below).
  The batch key includes the page, so a batch is entirely lightmapped or entirely vertex-lit. A lightmapped face gets no
  static vertex light or light subdivision; its batch's draw group (one per texture and page,
  [face draw groups](INDOOR_FACE_DRAW_GROUPS.md)) carries a second static vertex stream of lightmap UVs
  (`a_texcoord4`, computed from the face's affine map) and draws with `vs_indoor_textured_baked` /
  `fs_indoor_textured_baked` (`fs_indoor_textured_lit.sc` built with `INDOOR_BAKED=1`; with surface materials,
  `fs_indoor_textured_baked_materials`). Vertex-lit batches use the unchanged programs, so a map without a bake has no
  new per-face or per-frame cost: no extra stream, texture, program or branch. Toggling `lightmaps` rebuilds the
  batches once.
- **Shading**: the lightmap replaces `room ambient + 2 * vertex light` (`indoorStaticLight`); dynamic lights from the
  light grid (torch light, spells, projectiles, effects) add on top as before, with the same facing response; the sum
  is clamped to 2 as before. Lightmapped batches skip the static vertex-light refresh.
- **Actors, decorations, items** keep the light grid's static and dynamic lights, but their room ambient
  (`IndoorLightingFrame::sectorAmbient`) is the bake's actor ambient for the sector, so a monster in a dim, bounce-lit
  room is as dim as its walls. Decorations also subtract the frame ambient, so in a room lit mostly by bake-only light
  they come out much darker than the walls. A map can opt into MM9's model lighting instead (scene `model_lighting`,
  [indoor model lighting](INDOOR_MODEL_LIGHTING.md)): world ambient + ModelAdd + the BLV lights at full colour with
  `1 - d^2/r^2` and N·L, independent of the bake.
- **Doors and other linear movers** (2026-10-30): a face that exactly one door moves, every vertex of it (it moves
  rigidly), with a travel of at most `IndoorBakedMoverMaxTravel` (1024 units) is baked in the BLV's **stored pose**
  (`indoorMoverFaceBakeable`, used by the scene export). At runtime such a face samples its lightmap while its current
  vertices are one translation `t` of the stored ones, its lightmap UVs taken at `p - t`, so the light moves with the
  face: a door that slides into a lit or dark area keeps its stored-pose light (accepted for doors and panels). The
  lightmap UV stream is static; a moving face's position updates leave it valid, and a mover in a lightmapped batch
  takes no static vertex light. Before this, mover faces were vertex-lit and drew about twice as bright as the baked
  walls beside them. Stay vertex-lit (native static lights, room ambient, as before): faces that stretch as a door moves
  (frames, sills; MM6–MM8 door frames), faces two doors move, movers that travel farther than 1024 (a lift crossing
  rooms would carry one room's light into another; its vertex light follows it), any mover whose current pose is not
  one translation of its stored pose, and every mover of a sidecar baked before 2026-10-30 (no page: exactly as
  before). Movers the bake leaves out cast in their load pose (doors closed, so no light leaks under a closed door; an
  opened door does not let baked light through); baked movers cast in their stored pose (MM9's authored-open doors are
  stored shut). The texture mapping rule for door faces is separate and unchanged (`indoorMoverFaceKeepsStoredTexels`).
  Rotating movers follow the same rule through their rigid motion
  ([rotating movers](INDOOR_ROTATING_MOVERS_AND_LADDERS.md), "Baked lighting on rotating faces").
- **Not baked**: lights an event switches (a bake keeps a light as the map starts; an event's `SetLight` or
  `SetSectorAmbient` changes only vertex-lit faces and actors' grid lights), decorations' shadows (3D props do not
  cast yet), texture cutouts (a grate's face casts as solid), faces with the `IndoorSky` attribute (vertex-lit, neither
  cast nor receive; the MM9 dungeons' sky faces are ordinary faces with a sky texture and are profile emitters).

## Performance (Anskram Keep, 1600 × 900, visible window, VSync off, desktop GPU)

Medians of the per-second `[FramePerf]` samples (10 s per run, `tools/run_game.sh --visible`), the bake against
`--set video.lightmaps=false` on the same build and poses:

| Pose | Loop µs baked / unbaked | CPU p50 µs | GPU p50 µs |
| --- | --- | --- | --- |
| South hall | 312 / 290 | 291 / 274 | 237 / 224 |
| Central hall | 282 / 268 | 253 / 244 | 205 / 192 |
| North hall | 271 / 264 | 244 / 244 | 195 / 198 |

The lightmap costs at most about 15 µs of GPU and 20 µs of frame per frame here (one more texture fetch per pixel, a
second vertex stream and 21 more batches); the vertex-lit maps have no change in their path.

## Review

`level_generation/projects/mm9r_anskramkeep/review/lighting_v01_compare.jpg`: the 18 views of the v02 tour, MM9's
original map with its own lightmaps | the native BLV unbaked | the native BLV baked (`review_lighting.py tours|sheet`,
shots in `review/lighting_v01_{original,native,baked}/`). The bake gives the pools of light around the torches, the
pillars' shadows on the halls' floors and the darker corners the vertex light could not; MM9's original is evenly lit
(its 408 fill `DirLight`s and the 3 072-radius `Light6`, which the conversion leaves out) and shows its props.

2026-10-30 rebakes (movers, `emitters`, extra lights) of the three MM9 dungeons, each against MM9 and the previous
bake, mean brightness of the review tour (centre crop, `level_generation/projects/mm9r_common`
`python3 -m dungeon.sheet --brightness`): Anskram Keep 46.2 / 48.0 / 47.3 (`Light6` as an extra light lifts the
central hall to MM9's), Temple of Honk 122.9 / 123.6 / 123.9 (skylight halls 121–148 / 94–108 / 121–157), Lich Lab
39.1 / 48.0 / 39.9 (these MM9 figures include the view fade described under "References" below; the Lich Lab's true
mean is 31.9). Sheets `review/lighting_v0*_compare.jpg` and `_focus.jpg` in each map project. MM6–MM8: no map has
an indoor sidecar; door views in MM7 `7d06`, `7d08` and MM8 `d06` render identically before and after (only actors
and torch flicker differ).

**References (2026-10-30).** The "MM9 original" of these comparisons is our outdoor renderer drawing the old import,
and with `view_distance_scale: 0.4` it faded long views into the Enhanced sky: the Lich Lab's cross hall measured 100
with that fade and 34 without it. Calibrate only against tours run with `--set video.view_distance=unlimited`
(`level_generation/projects/mm9r_common/DUNGEON_PLAYBOOK.md`, "Reference runs"; `review/reference_fullview/` in the Lich
Lab, Temple of Honk and Anskram Keep projects). The Temple's references did not change; 12 of Anskram's 30 views did.

## Staleness

The game checks only the geometry identity (hashing the BLV is cheap; every dependency on each load is not).
`tools/lighting/stale_bakes.py [--assets <root>]` audits every installed `.lighting` of either kind against its
recorded dependencies (`tools/package_runtime_assets.py` `lighting_dependencies`), so a changed texture or scene file
is reported before a commit or release. Re-bake what it lists.

## Tests

- `./build/tests/openyamm_unit_tests --test-case='*indoor baked lighting*'`: parse, mapping, sector ambient,
  dependencies; stale geometry and counts; corrupt files; the per-map and per-face opt-in; which movers the bake
  takes (rigid, one door, short travel); a mover's stored-pose lightmap moving with it, and the vertex-lit fallback
  for a stretching mover and for a sidecar without mover data.
- `python3 -m unittest discover -s tools/lighting -p 'test_bake_geometry.py'` (chart grouping and basis).
