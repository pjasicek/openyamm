# Native baked outdoor lighting

The ClassicOdm renderer loads version-3 `.lighting` sidecars. New Sorpigal and Ravenshore have
generated data in their world `maps/` directories. This retains native geometry, textures, collision,
events and animated sprites. See [the implementation plan](../../../docs/BAKED_OUTDOOR_LIGHTING_IMPLEMENTATION.md)
and [validation status](STATUS.md) for completed checks and remaining acceptance work.

**Current focus: desktop New Sorpigal and Ravenshore.** Both installed bakes include the collinear-face fix
and the 315° sun with lighter shadows. The previously tested Android package predates these asset revisions.

## Rebuild

Run from the repository root. Requires Blender with Cycles and NumPy, and `/usr/bin/python3` with
PyYAML for reading authoritative scene metadata. Tested with Blender 5.2.2 LTS, CPU, 16 worker threads.
No Blender MCP connection, downloaded environment image or purchased assets are required.

```sh
blender --background --factory-startup --python-exit-code 1 \
  --python tools/lighting/cycles_fixture.py -- /tmp/openyamm-lighting-fixture

blender --background --factory-startup --python-exit-code 1 \
  --python tools/lighting/bake_outdoor.py -- \
  --profile level_generation/lighting/baked_outdoors/profiles/mm6_oute3.yml \
  --output /tmp/openyamm-lighting-mm6

blender --background --factory-startup --python-exit-code 1 \
  --python tools/lighting/bake_outdoor.py -- \
  --profile level_generation/lighting/baked_outdoors/profiles/mm8_out02.yml \
  --output /tmp/openyamm-lighting-mm8

cp /tmp/openyamm-lighting-mm6/oute3.lighting /tmp/openyamm-lighting-mm6/oute3.bake.json assets_dev/worlds/mm6/maps/
cp /tmp/openyamm-lighting-mm8/out02.lighting /tmp/openyamm-lighting-mm8/out02.bake.json assets_dev/worlds/mm8/maps/
```

Install both files from the same successful bake. `--python-exit-code 1` is important: Blender otherwise
can exit successfully after a Python exception. Keep intermediate `.npy` files outside version control.
Profiles use JSON syntax, which is a YAML subset. Use `--samples 16` for drafts and `--preview-only`
for the four sun-direction renders. Production profiles use 64 samples, two diffuse bounces and seed 17.

The existing `android/repack_runtime_assets.sh` packages all map files, including `.lighting` and
`.bake.json`; there is no extension whitelist to change. Repacking replaces the normal runtime ZIPs.
Development play uses `assets_dev` directly and does not require repacking.

## Authoring choices

### Batch bake MM6–MM8 outdoor maps

From the repository root:

```sh
python3 tools/lighting/bake_all_outdoors.py --output /tmp/openyamm-lightmaps-all --install
```

This enumerates the 42 current `.odm` files under `assets_dev/worlds/mm6`, `mm7` and `mm8` only.
It excludes BLV, MM9 and other worlds. Jobs run sequentially through the existing Blender producer.
Existing maintained map profiles are used where present; other maps inherit the New Sorpigal recipe
(315°/45°, sun energy 2.6, white sky energy 0.35, 64 samples). Runtime sky tint/strength and grading
remain settings, not extra factors applied during baking. One direction is a starting point for all
maps, not a separately reviewed sun direction for each map.

`--install` copies the lighting/recipe pair into the source map directory only after that map's bake
succeeds. Without it, all results remain under the output directory. Each map has its own world/map
folder with `profile.json`, `blender.log`, recipe, sidecar and the producer's reports/intermediates.
`batch-report.json` records successes and failures; a failed job does not stop later maps, and the
batch exits nonzero if any job fails. The producer's static-scene and encoding checks remain active.
Output must be outside `assets_dev` so a failed bake cannot overwrite an installed recipe prematurely.

Use `--dry-run` to list candidates without writing or baking, `--world mm6` to restrict the world,
or `--samples 16` for a draft. To retry only failures from a previous report:

```sh
python3 tools/lighting/bake_all_outdoors.py \
  --output /tmp/openyamm-lightmaps-retry \
  --retry-failed /tmp/openyamm-lightmaps-all/batch-report.json --install
```

Retries write `retry-report.json` and preserve the input report. To retry again, point `--retry-failed`
at that retry report and choose a new output directory. There is no implicit skip based on file
existence: without `--retry-failed`, every selected map is rebaked.

The first full user run produced 30 successes and 12 missing-material failures. The producer now
resolves native bitmap names through the same development-package order as the game: active world,
engine, then sorted other world packages, with case-insensitive texture names. This fixes cross-world
references such as MM6's `trim11_32` and MM7's `hhr1bwall`, without renaming textures or substituting
placeholder materials. The resolved file paths are recorded as bake dependencies. A material audit
found no unresolved face or terrain names in the 12 failed maps after this fix; full retry bake results
remain to be checked. Run focused tests with:

Version 3 is the only runtime format. To migrate installed legacy MM6–MM9 sidecars once, including a
linear-light 2048-to-1024 terrain conversion for paired bakes, run:

```sh
python3 tools/lighting/convert_lighting_v3.py
```

The converter updates paired bake recipes and their recorded dependency hashes. Newly generated files
already use version 3 and do not require this step.

```sh
python3 -m unittest discover -s tools/lighting -p 'test_bake*.py'
```

### Shared bake recipe

- Both maps use sun azimuth 315°, elevation 45°, angular size 2°. Both use sun energy 2.6 and white
  environment strength 0.35: more sky fill makes shadows lighter, while slightly less direct sun keeps
  exposed ground close to its previous brightness. Ravenshore now matches the New Sorpigal lighting profile.
  Azimuth goes from native +X toward +Y; +Z is up. The light rays point opposite the recorded sun vector.
  New Sorpigal was changed from 135° to 315° for the user's comparison of its prominent facades;
  elevation and source strengths were retained. The original four-direction previews selected 135°.
  Previews in `review/` precede the shoreline opacity fix;
  magenta shore regions in those previews are an exporter issue fixed in the installed bakes.
- Native positions are divided by 128 for Cycles. Native face fans and terrain diagonals are retained.
  Geometry is never subdivided. Scene face attributes and terrain lookup tables are applied.
- Buildings: 32 world units/texel, a 1024-pixel page limit, four-pixel chart borders and three-pixel dilation.
  Charts are packed largest-first into deterministic shelves and each page is cropped to its occupied width
  and height. Very large charts are reduced to fit. Terrain: one 1024² atlas over the full 127-cell domain
  (about 63.5 world units/texel). Every receiver bake sees the entire map's geometry. Version-3 page payloads
  use lossless repeated/literal RGBM texel spans.
- Original opaque geometry, including terrain casting onto terrain, casts shadows. Magenta building cutouts are transparent. Shore cutouts
  and animated water use a fixed, dark water material for bounce; no water animation is baked.
  Sprites, grass meshes, transient effects and local lights do not cast permanent baked shadows.
  Maps with authored moving mechanisms or unsupported terrain attribute overrides are rejected.
- Probes: 512-unit XY grid, refined to 128 units around building bounds; terrain-relative heights
  96/384/1152. They sample upward-facing diffuse illumination. Four nearest samples are interpolated
  after geometry visibility checks. This approximates shelter; it is not a sharp character shadow map.
  Outside supported probe coverage, sprites receive sky-only fill.
- Static probe results are cached by exact position with a bounded 8192-entry cache. Clock weights and
  local lighting remain live. The cache belongs to the map view and is cleared with its resources.

## Runtime contract

[FORMAT.md](FORMAT.md) describes the binary extension. Sun and environment illumination are separate
linear RGBM4 textures. Runtime decodes and adds them, then adds existing point lights; it never multiplies
a torch by a dark baked shadow. Receiving texture albedo is applied once. The fixture checks this and
the retention of colored bounce. The existing display-encoded texture pipeline uses a 2.2 gamma
approximation for the new path; this does not convert the entire renderer to an HDR pipeline.

Sun intensity follows daylight and twilight, reaching zero at night. Environment weight fades to 0.12.
This is a fixed-direction approximation, not a moving sun. Fog, secret-face highlighting, water
animation and local lights remain runtime effects. There is no per-frame shadow-map pass or GI tracing.
Probe visibility uses the existing CPU geometry LOS query on cache misses.

Version-2 sources can be tuned without rebaking through `[video]` settings `baked_sun_strength`,
`baked_sky_strength` (0–16; defaults sun `1`, sky `3`), `baked_sun_color` and `baked_sky_color`
(comma-separated linear RGB in 0–1; defaults sun `1,1,1`, sky `0.8,0.9,1`). Cinematic grading defaults
to enabled at `60%`. Explicit values in existing INIs are preserved. The multipliers apply after clock
weights to surfaces and sprite probes,
including the sky-only probe fallback. Raw probe caches remain valid when tuning. For live changes use
`config set baked_sky_color 0.8,0.9,1` or `config set baked_sky_strength 1.5` in the debug console;
these also save the active settings file. File edits are read on launch. Sky strength also scales night fill.
These controls do not recolor the visible sky texture or fog. Sun direction and changes to occlusion or
directional environment illumination still require rebaking. See the
[tavern comparison handoff](../../../docs/TAVERN_LIGHTING_MATCH_IMPLEMENTATION.md) for the experiment.

Pages use linear byte textures with the existing Lightmap sampler profile, clamped edges and **no mipmaps**.
Do not generate generic atlas mips: they would mix neighboring charts and incorrectly filter RGBM.
Version-1 MM9 pages retain their previous shader semantics and brightness scaling. Unbaked maps retain
their previous shaders and do not allocate lightmap resources or perform probe lookups.

The loader checks geometry identity and all declared dependencies: native map, scene metadata, terrain
registry, texture files and the installed recipe. Missing/corrupt/stale declared data rejects map loading
with a regeneration error. A map without a sidecar is valid. After changing source assets, rebake;
after changing a profile or producer, regenerate and install its new recipe and sidecar together.

## Checks

```sh
cmake --build build --target openyamm openyamm_unit_tests -j25
python3 -m unittest discover -s tools/lighting -p 'test_*.py'
./build/tests/openyamm_unit_tests --test-case='*outdoor lighting*,*outdoor sunlight*'
./tools/run_game.sh --isolated baked_sorpigal --world mm6 --map oute3.odm
./tools/run_game.sh --isolated baked_ravenshore --world mm8 --map out02.odm
```

`review/validation/load_*.yml` contains load/save/clock smoke scenarios. Pass the matching `--world`
explicitly. MM7 Emerald Island is `7out01.odm`; plain `out01.odm` names MM8 Dagger Wound Island in the
merged registry. Xvfb captures establish appearance only; hardware performance comes from desktop runs.

For an independent New Sorpigal terrain self-shadow check after baking:

```sh
blender --background --factory-startup --python-exit-code 1 \
  --python tools/lighting/terrain_shadow_audit.py -- \
  /tmp/openyamm-lighting-mm6/terrain_sun.npy /tmp/terrain-shadow-audit.json
```

The audit uses terrain-only rays against the native triangles, independently of Cycles, and compares
triangle-center illumination against unoccluded direct sunlight using the current New Sorpigal profile.
