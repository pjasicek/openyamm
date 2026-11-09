# Terrain decoration profiling and batching

The avoidable slowdown came from submitting each visible terrain cell separately. At the reported New Sorpigal
camera that produced 148 decoration draws for 8,714 instances. The optimized path joins contiguous visible instance
ranges when their mesh kind and all light uniforms are identical: 14 draws for the same 8,714 instances.

The culling boundaries, placement data, density, grass variants, animation, shader code, texture atlas, draw distance
and fade remain the same. No per-frame instance uploads or new GPU buffers are introduced. Different light uniforms,
mesh kinds and gaps in the instance ranges terminate a batch. Light selection uses each visible cell's bounds when the cached batches are refreshed.

## Batching diagnosis (before the 20 Hz cache)

Release build, desktop display `:1`, NVIDIA RTX 3060 Ti, OpenGL, 1600×900, VSync off, accepted enhanced trial assets,
and the existing terrain reference save. Party foot position `(-9728, -11319, 161)`, yaw `4.758` radians,
pitch `-6.274` degrees. The recorded rendered eye position was `(-9728, -11319, 337)`; camera position and direction
remained constant throughout the sequence.

Temporary instrumentation cycled through disabled (phase 0), per-cell submission (phase 1), and merged submission
(phase 2), five seconds per phase, within one game process. Measurement followed five seconds of warmup and lasted
forty seconds. This avoids comparing only separate game launches. The original-submission control used the same
light selection code and disabled only joining compatible ranges. Whole-frame timers came from bgfx's asynchronous
OpenGL GPU queries and render-thread statistics. Decoration CPU timing surrounded its culling/selection/submission
block. Samples spanning phase boundaries were excluded using their fractional draw counts.

Medians of the retained approximately one-second samples:

| Measurement | Disabled | Original cell draws | Merged draws |
|---|---:|---:|---:|
| Frames per second, approximately | 2252 | 1778 | 2218 |
| Decoration CPU work | <0.001 ms | 0.091 ms | 0.046 ms |
| Whole-frame renderer/driver CPU interval | 0.369 ms | 0.483 ms | 0.373 ms |
| Whole-frame GPU elapsed interval | 0.318 ms | 0.437 ms | 0.331 ms |
| Decoration draws | 0 | 148 | 14 |
| Submitted decoration instances | 0 | 8714 | 8714 |
| Retained samples | 8 | 12 | 12 |

The roughly 21% median FPS penalty in this run fell to roughly 1.5%. Exact percentages vary: individual one-second
rates ranged 1928–2350 off, 1457–1863 original, and 1978–2274 merged. This is a result at this camera on this desktop,
not a guaranteed cost on every map or device. GPU elapsed intervals can include gaps while waiting for submitted
commands; they are not isolated grass-fragment execution times. CPU/driver/GPU intervals overlap and must not be added.
The unchanged instance count and large reduction in submission/driver cost identify draw-call overhead as the main
avoidable expense here.

Raw evidence: [sequence log](profile_sequence.log), [run record](profile_sequence.json),
[medians/ranges](summary.json), [GPU identification](renderer-info.txt).
All temporary phase switches and timing counters were removed from the final source and rebuilt executable.

## Correctness checks

Ten focused tests, 38,508 assertions, passed. New batching coverage rejects empty batches, noncontiguous or overlapping
ranges, different grass/stone meshes, and differing light positions, colours or shader parameters. Existing placement,
mask, variant, culling, settings and alpha-coverage checks still pass. Camera movement, projection changes and
renderer shutdown invalidate the cached view; this is covered by an additional test.

Native-renderer screenshots at the same requested camera were inspected:
[before](grass_batching_before.png), [after](grass_batching_after.png). Placement, grass density, lighting and silhouettes
match; wind/ordinary scene animation may differ between captures. These two visual captures used Xvfb at 1600×1200
and were not used for the desktop GPU performance measurements.

Both `build/game/openyamm` and the isolated ground-cover trial executable were rebuilt/refreshed. The runtime console
command remains `config toggle terrain_decorations`. All timed profiling game processes exited after their runs.

## Reduced update frequency

After batching, separate uninstrumented runs measured about 2,039 FPS on and 2,348 FPS off (13% difference),
showing why the earlier within-process 1.5% result must not be treated as a universal final cost. Records:
[on](final_on.json), [off](final_off.json). Their CPU world-render difference was about 0.056 ms/frame.

Following the user's suggestion, the final code caches the visible draw ranges and selected light uniforms, refreshing
at 20 Hz while the camera is stationary. Camera movement/rotation, projection changes, and added/removed light sources
refresh immediately. This avoids delaying newly visible grass during turning or movement. Existing moving/flickering
light uniforms can be up to 50 ms old while stationary. Grass wind, fog, geometry and draw submission still update
every frame. Frustum trigonometry is computed only when the view changes; range tests use squared distances.
The cached vector retains capacity across updates and is cleared when the map unloads.

Separate final cached-build launches measured **2,243 FPS on / 2,122 FPS off**. The reversal is evidence of
launch-to-launch clock/load variation, not a claim that grass makes rendering faster. Records:
[cached on](cached_on.json), [cached off](cached_off.json). Both runs used four seconds of warmup and twelve seconds
of measurement, and exited cleanly. A final within-process on/off cross-check follows below.

The final cached build was also checked while moving: [start](grass_cached_motion_still.png),
[walked forward](grass_cached_motion_moved.png), [continued movement](grass_cached_motion_turned.png).
The ordinary draw range and grass coverage remain intact. No temporary instrumentation is needed by the cache.

## Final within-process cached comparison

A temporary five-second alternating draw enable ran in one process for forty measured seconds after five seconds
of warmup. The first FPS sample of each phase was excluded to avoid mixing on/off intervals. This final cross-check
measured **2053 FPS cached on / 2278 FPS off**, approximately **9.9%** lower FPS
or **0.048 ms/frame** added at this camera. Raw results:
[cached sequence](cached_sequence.log), [run record](cached_sequence.json), [summary](cached_sequence_summary.json).
The temporary switch and its log line were removed and the normal build restored afterwards.
