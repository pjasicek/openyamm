# Baked outdoor lighting: implementation and validation

Updated 2026-09-16. **Desktop New Sorpigal and Ravenshore both have the corrected complete-face bake,
315° sun and lighter shadow settings.** The last Android APK predates these asset revisions.

The native producer, runtime and installed bakes exist for **New Sorpigal and
Ravenshore**, including terrain, building faces and actor samples. This is a working first implementation;
the full visual/performance acceptance matrix in the plan is not yet signed off.

## Implemented

The first MM6–MM8 batch completed 30 maps and failed on 12 missing-material lookups. The exporter now
uses merged world-package texture lookup like the runtime. All face/terrain material names in those
12 maps resolve in a post-fix audit; the full retry bakes are pending. Use the README's `--retry-failed`
command to retry just those entries without repeating the successful maps.

- Reproducible Cycles CPU export/bake of the original terrain and building geometry. Separate sun and
  sky diffuse illumination, colored bounce, original cutout opacity, planar building charts, full-map
  terrain coverage and spatial actor samples. No new art is required.
- Version-2 RGBM4 storage, validated geometry/dependency identities, paired atlas upload and source weights.
  Fixed sun direction; daytime intensity fades at night. Local torch/spell lights remain additive.
- Runtime sun/sky RGB and strength multipliers in `[video]` settings, with the selected sky preset and live
  `config get|set` console access. Both surfaces and sprite probes use the same factors without rebaking.
  See the [tavern handoff](../../../docs/TAVERN_LIGHTING_MATCH_IMPLEMENTATION.md) for usage and limits.
- ClassicOdm static building batches preserve lightmap UVs and split by material **and atlas page**.
  Animated textures and event face overrides still use the existing resolution path.
- Cached actor probe interpolation with geometry visibility checks. Grass receives terrain illumination.
  No runtime world shadow-map rendering or GI tracing is added.
- MM9 version-1 data/shading stays separate. Maps without sidecars keep the ordinary shaders.
- Canonical world ZIP mounts make qualified bake dependencies readable without mounting the same archive
  twice. Android shader extraction reads the APK directly, avoiding obsolete internal copies shadowing it.

See [README.md](README.md) for generation, installation, authoring limitations and runtime commands;
[FORMAT.md](FORMAT.md) specifies the binary contract.

The [15-preset runtime sweep](review/mm6_oute3/runtime_sweep_20260916/README.md) captures both requested
New Sorpigal cameras for all candidates. Preferred daylight values: sky `0.8,0.9,1` at strength `3`,
white sun at strength `1`, cinematic grading `60%`. The user selected this preset as the default;
engine defaults and the active INI now use it. Existing explicit INI choices remain respected.
Night and cross-map visual acceptance remain separate.

## Defects found during review

The user's `test_img/1321.png` exposed a real missing connection: the original implementation prepared
building lightmaps but ClassicOdm static draw groups discarded them and submitted the ordinary shader.
The corrected grouping/upload/submission now uses the baked building shader. Earlier screenshots and
performance reports are retained under each map's `before_building_draw_fix/`, explicitly superseded.
They must not be used to claim building lighting worked before this fix.

A second defect exposed by `1322.png`–`1325.png` was in the exporter: it classified a face as degenerate
using only its first three vertices. **256 valid New Sorpigal faces have a collinear prefix**. The exporter
now uses the largest nondegenerate native fan triangle for its chart basis. Four Python regression tests
cover collinear/duplicate prefixes, fully degenerate faces and winding. The installed rebake covers all
2,869 visible faces; only the 13 native invisible faces lack pages. See
[face coverage](review/mm6_oute3/face_coverage.json).

Terrain is both caster and receiver. An independent terrain-only BVH ray audit of triangle centers
found 167 terrain-occluded samples facing the current 315° sun. Their median baked sunlight is about 0.1% of the
unoccluded direct expectation, versus about 100% for unoccluded samples. This confirms terrain-on-terrain
shadows in the bake. At 45° elevation they occupy small areas; Lambert shading on slopes is a separate
contribution. [Audit results](review/mm6_oute3/terrain_shadow_audit.json) include native sample/blocker positions.

Complete-face bake views at the previous 135° azimuth:

- [Training grounds windows](review/mm6_oute3/baked_facefix_training_street.png).
- [Well and bridge](review/mm6_oute3/baked_facefix_well_bridge.png).
- [Temple front](review/mm6_oute3/baked_facefix_temple.png).
- [Terrain shadow below the coastal hill](review/mm6_oute3/baked_facefix_terrain_coast.png), with ordinary
  hostile actors/projectile lights active. This is appearance evidence, not an isolated lighting benchmark.

The following earlier views include the building draw fix but predate the complete-face rebake:

- [New Sorpigal porch and opposite facade](review/mm6_oute3/baked_bmodels_sorpigal.png).
- [Ravenshore building faces](review/mm8_out02/baked_bmodels_ravenshore.png).
- Night torch comparison: [before](review/mm6_oute3/baked_bmodels_torch_night_before.png) and
  [after](review/mm6_oute3/baked_bmodels_torch_night_after.png), cast through the normal spell UI.

These demonstrate native runtime shading, not a Blender preview. Existing texture-painted highlights
and shadows remain in the original albedo; baking cannot remove them or add missing geometric ornament.

## Softer New Sorpigal shadows

New Sorpigal was rebaked with sky energy **0.35** (previously 0.25) and sun energy **2.6**
(previously 3.0). This lifts shade while keeping exposed horizontal surfaces at similar brightness.
Shadow direction, geometry, atlas resolution and runtime rendering cost are unchanged. Previous
`baked_facefix_*` captures document the darker profile; the
[new training-ground capture](review/mm6_oute3/baked_softer_training.png) uses this revision.
Comparing float atlas samples through the display gamma approximation, selected shaded samples are
about 14–16% brighter, while selected sunlit samples stay within 1% of their previous brightness.
The terrain self-shadow audit still passes.

## Sun-direction comparison

The user requested New Sorpigal azimuth **315°** for direct comparison with the previous **135°** bake.
Elevation remains 45°, sun energy 2.6, sky energy 0.35, angular size 2°. The existing screenshots above
show the previous direction; this revision is installed for the user's in-game comparison.
The previous softer 135° reports and recipe are retained under `review/mm6_oute3/sun135_softer/`.

## Ravenshore matching bake

Ravenshore was regenerated at the user's request with the same **315° azimuth, 45° elevation,
sun energy 2.6 and sky energy 0.35**. This also applies the collinear-face exporter correction:
all **6,024 eligible visible faces** now have atlas entries, fixing the 205 missing faces in its
previous bake. See [face coverage](review/mm8_out02/face_coverage.json). Existing Ravenshore screenshots
predate this rebake. Previous reports and recipe are retained in `review/mm8_out02/sun135_initial/`.

## Generated data

| Measurement | New Sorpigal | Ravenshore |
| --- | ---: | ---: |
| Atlas payload, CPU copy and GPU texture storage each | 48 MiB | 64 MiB |
| Sidecar disk size | 52,793,887 bytes | 70,580,866 bytes |
| Actor probes | 61,752 | 83,289 |
| Sum of measured Cycles bake passes | 39.23 s | 51.39 s |
| Maximum linear RGBM encoding error versus float intermediate | 0.001809 | 0.001776 |

Atlas figures exclude driver overhead, geometry, probe vectors/spatial indices and the bounded lookup
cache. Bake durations exclude export/material/chart preparation and are not end-to-end timings;
concurrent work also prevents interpreting them as isolated backend benchmarks. Retained `bake_report.json`
and `encoding_report.json` give exact records. Blender 5.2.2 LTS, CPU/16 threads, 64 samples, seed 17,
two diffuse bounces, 1024² building pages and 2048² terrain were used for both maps.

## Completed checks

- Desktop `openyamm` and focused unit targets build. **37 cases, 338 assertions pass** for asset mounting,
  lighting format/probes and sunlight weights. Tests include malformed data, page pairs, source
  separation, dependency traversal, negative probes, strict v3 compression and obsolete-version rejection.
- Cycles floor/wall fixture passes receiver-albedo exclusion, colored bounce and sun-shadow checks.
- Both maps pass headless load/save, clock advance, reload and leave/re-enter scenarios (12 steps each).
  Unbaked MM7 Emerald Island (`7out01.odm`) and imported MM9 Thjorgard also pass smoke scenarios.
- Packaged world ZIP load succeeds. Deliberately changing the declared recipe rejects the stale bake.
- Legacy MM9 fragment shader compiled from HEAD and the new macro-disabled shared source produce the
  same binary SHA-256: `157dfcc52acbd4cb15103d2d55901c7d095a1fa18966523e89ce00ad4f375eef`.
  This verifies shader preservation, not a substitute for exhaustive MM9 gameplay testing.
- Android release x86_64 emulator initially passed both maps, one suspend/resume cycle and all 28 APK
  shader-byte comparisons. Both were rerun successfully after the static-building draw fix.
  The later corrected bakes and sun-direction changes were installed in desktop development assets only.

Logs and repeatable scenarios are in [review/validation](review/validation).

## Remaining acceptance work and limits

- Physical Android/ARM64 device performance and memory acceptance have **not** been established.
- Full matched walking/flying routes with CPU/GPU timing, raw frame-time p50/p95, draw/triangle counts
  and an agreed hardware budget remain outstanding. Launcher FPS samples do not provide those statistics.
- Current elevated comparisons use timed ascent; actual flight Z was not measured. They are visual
  coverage, not exact matching camera evidence. Ground captures record requested Z as a collision hint.
- Review the final building path across the complete doorway/temple/dock/coast matrix, twilight transition,
  and moving actors crossing shelter boundaries. Unit tests cover source fading and wall-rejected samples;
  they cannot certify every visual seam or probe transition.
- Both maps are testing 315°/45°, pending the user's comparison. This is not final art direction. Low-resolution
  charts and scalar upward-facing actor probes are deliberate first-pass approximations.
- Sprites/foliage do not cast permanent shadows. Dynamic occluder shadows, moving sun, normal-map response,
  terrain LOD and new geometry/materials remain outside this implementation.

Work-package status: P1 code and both corrected bakes are implemented; P0/P2/P3/P4 have substantial evidence but retain the visual
and measurement gaps above. P5 has release-emulator coverage, with physical target acceptance pending.
