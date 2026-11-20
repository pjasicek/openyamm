# Asset loading implementation — 27 September 2026

**Update 2026-09-27:** The raw atlas cache described in this historical measurement is superseded by
[source-free GPU-compressed deployment](../../level_generation/creatures/SPRITE_RUNTIME_DEPLOYMENT.md).
The loading-readiness and residency changes remain; the old raw-cache sizes and cooker CLI below
are historical results, not the release asset contract.


This implements the five loading workstreams from the [investigation](ASSET_LOADING_INVESTIGATION.md): indexed lookup
and cheap dimensions, presentation readiness, shared residency, bounded preparation, and offline atlas cooking. Destination
prefetching remains a separate follow-up. No OpenEnroth or mm_mapview2 code was copied.

## Measured result

Release desktop build, OpenGL, NVIDIA RTX 3060 Ti 8 GiB, driver 595.91.07, current loose x2 assets, warm OS filesystem
cache. The baseline was rebuilt from a source/header snapshot taken before this implementation, retaining the user's
existing changes. Both builds used the same source save, settings and current assets. Private benchmark binaries drove
ordinary pending map transitions after two seconds of gameplay; instrumentation is outside the repository.

| Operation | Before | After, selected two-worker limit |
| --- | ---: | ---: |
| Process launch to loaded New Sorpigal | 22.82 s | 4.60 s |
| First entry into Goblinwatch | 3.20 s | 1.09 s |
| Return to New Sorpigal | 5.99 s | 1.58 s |
| Second entry into Goblinwatch | 3.01 s | 0.87 s |
| Second return to New Sorpigal | 5.98 s | 1.42 s |

Transition numbers include the entire transition frame and loading readiness, not only the map parser. Launch timing
comes from the desktop supervisor's loaded-scene observation. These are short route measurements, not p95 statistics,
cold-disk results or Android results. [Machine-readable observations](../../tools/asset_loading/benchmark_20260927.json).

The default route uploaded 15 atlas pages on startup and five additional pages on first indoor entry. All three later
transitions uploaded **zero atlas pages and zero ordinary billboard textures**. Resident atlas payload was 648.27 MiB
and native billboard allocation was approximately 119.21 MiB after visiting both maps. Geometry, HUD, driver allocations,
CPU buffers and upload staging are additional; these numbers are not total VRAM or peak process memory.

The baseline had 139 and 154 ms gameplay frames dominated by `bgfx::frame` after returning outdoors. The selected
optimized route had one 20.3 ms gameplay frame above the 16 ms trace threshold. Four-worker and eight-worker experiments
also observed isolated 30.5 and 57.5 ms render-thread waits. The change removes the measured repeated asset work and
first-HUD preparation from gameplay; it does not establish that every future frame or interaction is hitch-free.
Screenshots were excluded from the timing routes. A final normal-build smoke reached New Sorpigal in 4.40 s,
with no asset errors and one 19.4 ms gameplay frame above the trace threshold.

## Measured RAM and GPU memory

A separate paired run measured the original and final two-worker builds through the same five-map route at 1600×900.
Each stop ran for eight seconds; settled values below are medians after the first three seconds. RAM is process RSS
from Linux `/proc/PID/status`, with peak RAM taken from the kernel's `VmHWM`. GPU memory is NVIDIA's per-process
graphics framebuffer accounting for the game PID, sampled every 100 ms. Other desktop applications are excluded.
The source save and normalized rendering settings match. Both runs exited successfully and used no swap.

| Point in route | Before RAM | After RAM | Before GPU | After GPU |
| --- | ---: | ---: | ---: | ---: |
| Initial New Sorpigal | 1.91 GiB | 1.78 GiB | 867 MiB | 867 MiB |
| First Goblinwatch visit | 1.41 GiB | 1.32 GiB | 379 MiB | 737 MiB |
| First return to New Sorpigal | 1.74 GiB | 1.47 GiB | 849 MiB | 928 MiB |
| Second Goblinwatch visit | 1.52 GiB | 1.33 GiB | 385 MiB | 781 MiB |
| Second return to New Sorpigal | 1.88 GiB | 1.48 GiB | 809 MiB | 928 MiB |
| Peak across the route | 2.23 GiB | 2.16 GiB | 875 MiB | 928 MiB |

Retaining sprites costs GPU memory after travel, especially indoors where the old build released the outdoor sprites.
At the final outdoor stop RAM was about 405 MiB lower and GPU memory 119 MiB higher. The sampled GPU peak increased
53 MiB, remaining below 1 GiB on this route. Logical texture payload counters and the driver's physical framebuffer
accounting are distinct measurements; the retained-payload figures above should not be added to this GPU total.

The **7.762 GiB cooked library is disk storage** across all installed creature packages. It is not loaded into RAM or
VRAM as a whole. The cache budgets below cover specific retained resources; they are not caps on total application
memory, and active-level resources can exceed their retention budget.

This is one short matched route, not a worst-case map survey or a long-session leak test. The 100 ms GPU sampling can
miss shorter peaks. RSS includes resident shared mappings and allocator/driver buffers; it is not an exclusive heap
measurement. No Android or integrated-GPU memory claim follows from these desktop numbers.
[Machine-readable memory measurements](../../tools/asset_loading/memory_20260927.json) include exact values, ranges, binary
hashes and the method. Raw samples and private instrumentation remain under `/tmp/openyamm-loading-implementation/`.

## Implemented ownership and ordering

1. **Indexed lookup and dimensions.** `AssetFileSystem` owns synchronized case-folded directory indexes and positive /
   negative file resolutions. Exact names, package priority and icon package policy are preserved. Same-package case
   ambiguities are rejected; different mounted packages follow mount precedence. Mount changes, world switches, explicit
   refresh, editor reload and the runtime `reload map` command invalidate the generation. Item dimensions use validated
   PNG/BMP/PCX headers and per-item-table memoization, preserving logical scale and inventory sizing.
2. **Readiness before gameplay.** The finalized world and real HUD render twice to a hidden target with zero elapsed
   time and idle input. The preparation path skips gameplay input, simulation, screenshot requests and audio feedback.
   It reconciles actor atlas animations after save/event setup, prepares all animation frames of active named effects
   including delayed components, and prepares selected map models. The overlay remains visible until the warm render's
   GPU readback completes on supported backends. The real HUD discovers minimap, portraits and dynamic widgets here.
   Platforms without texture blit/readback receive the two presentation passes but have no equivalent readback fence.
3. **Session residency.** `GameApplication` owns both the atlas cache and native sprite texture cache; indoor and outdoor
   renderers hold references. Renderers release their map state, while retained textures survive. Content generations
   invalidate across worlds/policy changes. Map-local decoration overrides carry their explicit source path, so identical
   sprite names in different maps cannot reuse the wrong art. Active resources stay pinned; older resources are evicted
   by use and bytes. The map loader also keeps a bounded decoded-image working set, while discarding source-file buffers.
4. **Bounded CPU preparation.** Missing cooked pages are read, validated and prepared on up to two workers (also bounded
   by half the reported hardware concurrency), with an estimated 256 MiB input/output staging limit. One oversized page
   is allowed to make progress. Workers never mutate rendering caches or publish bgfx resources. Publication remains on
   the owning thread; pending futures join before load failure can release their inputs. Existing native sprite decode
   parallelism remains in place. PNG decoding requests RGBA bytes and performs a direct channel swap, avoiding the
   previous generic floating-point BGRA conversion. Map/surface preparation and contextual audio are not all parallelized.
5. **Offline cooking.** The host cooker runs the existing per-cell atlas packing, padding, alpha-aware mip filtering and
   hit-mask construction. Runtime `.oyatlas` pages contain lossless BGRA/mask mip bytes, frame rectangles and compact hit
   masks. Runtime loads perform no PNG inflation, atlas packing or mip construction for these pages. Version, manifest
   fingerprint, source size/time, dimensions, frame identity, payload hash and truncation checks reject stale/broken data.
   Archive source timestamps are exempt from exact comparison because ZIP timestamp precision differs; packaging verifies
   the cook first. Runtime does not silently regenerate stale pages.

Game state, respawn/save application and Lua event ordering remain synchronous. Warming presentation does not run the
map's on-load events a second time. Shared gameplay UI retains its existing session lifetime.

| Retention budget | Desktop | Android defaults |
| --- | ---: | ---: |
| Atlas GPU payload | 768 MiB | 256 MiB |
| Native billboard GPU textures | 128 MiB | 32 MiB |
| Decoded map bitmap cache | 128 MiB | 32 MiB |

These are retention budgets, not hard limits on an active map's required resources or total application memory.
In the private 128 MiB atlas-retention test, pages alternated between the outdoor map's 15 and indoor map's nine pages;
active resources remained available and evicted pages were reloaded behind readiness. Outdoor return time increased to
1.82–1.91 s. The focused native-cache test also covers pinning, eviction, palette/source identity and refresh.

Two/four/eight-worker launch measurements were 4.60/4.70/4.81 s. Peak estimated atlas preparation bytes were 178/252/252 MiB;
the byte limit constrained the eight-worker experiment to four actual jobs. This short comparison does not establish a
statistically meaningful speed difference. Two workers are the conservative default because they used less staging
memory with comparable wall time. Ordinary map-data buffers and bgfx upload copies are outside this staging estimate.

## Build and packaging

Normal host game builds prepare changed runtime pages automatically:

```sh
cmake --build build --target openyamm -j25
./build/game/openyamm_sprite_atlas_cook assets_dev --verify
```

The first cook generated and verified **237 pages**, occupying **7.762 GiB uncompressed** across the installed creature
library. These derived directories are ignored by git. Subsequent builds check stamps and retain unchanged pages.
`--force` rebuilds all pages; `--verify` checks their stamps and runtime payloads. Increment the cook format version when
changing packing/filtering semantics. PNG sources remain authoritative. GPU-native compression is not introduced here.

The raw v1 representation is not an acceptable final shipping footprint. The subsequent
[compact atlas format review](ASSET_ATLAS_FORMAT_REVIEW.md) measures a 1.17 GiB lossless alternative across all 237 pages
and smaller native ASTC samples, and proposes removing duplicate authoring assets from release packages. Those probes
have not yet replaced the runtime format described here.

`android/repack_runtime_assets.sh` now builds the host cooker, cooks and verifies before creating ZIP packages. Use
`OPENYAMM_HOST_BUILD_DIR` if the configured host build is somewhere other than `build`. Cross-compiled builds do not run
a target-platform cooker. Any other packaging workflow must include these generated runtime pages after a successful
cook/verify; ZIP creation alone does not create them. Full packaged-game performance and Android Release remain untested.

Strict cooking exposed four already installed manifests whose declared linear palette schema contained lookup tables.
The MM6 exporter now normalizes those authored tables into the existing explicit LUT schemas. An explicit migration
updated `mm6_hrp`, `mm6_hyd`, `mm6_lzd` and `mm6_min1`, preserving artwork, crops and palette values. The migration tool is
[tools/migrate_sprite_atlas_palettes.py](../../tools/migrate_sprite_atlas_palettes.py); hashes and generated lookup receipts are
in [palette_migration_20260927.json](../../tools/asset_loading/palette_migration_20260927.json). Do not rerun the receipt command
over the historical receipt after the migration has completed.

## Validation and remaining costs

- Normal game and unit-test targets build successfully. No Vulkan build or profiler permission change was needed.
- 82 focused C++ cases / 4,365 assertions pass, including concurrent asset reads, package precedence, dimensions,
  exact mip/hit-mask round trips, corrupt/stale payload rejection, delayed effect dependencies and real Noop-backend
  native texture lifetime/eviction. Three palette-export tests pass. All 237 installed cooked pages verify.
- MM6, MM7 and MM8 shared-FX map lifecycle scenarios pass (outdoor → indoor → outdoor).
- Native MM6 timing route and indoor check pass; native Emerald Island and Dagger Wound Island starts pass. Screenshots
  were inspected for world rendering, enhanced sprites/decorations and HUD/minimap presentation. Their launch observations
  were 3.1 s for direct Goblinwatch, 3.7 s for MM7 and 4.1 s for MM8; these are not matched baseline comparisons.
- A broader texture-name test selection has three failures: Darkmoor's native actor-preview texture-vector expectation,
  and Harm/Light Bolt tests requiring legacy loose BMP filenames. These tests/legacy assets were not rewritten as part
  of this performance change. All three tests were independently rebuilt against the original source/header snapshot:
  they reproduce the same 51 failed assertions before these changes. The focused tests above do not hide these failures.

The original 1–2 s startup / 250–500 ms transition goals are **not yet achieved**. The measured final outdoor reload still
spends roughly 0.95 s assembling map assets: terrain texture work ~258 ms, decoration work ~182 ms, sprite-object work
~136 ms, scene YAML parsing/application ~162 ms, actor previews ~81 ms and bmodel textures ~77 ms. Renderer/world setup
adds roughly 450 ms. These stage timings include copies, preparation and progress pumping as well as reads; they are
not decode-only profiles. Atlas preparation and ordinary billboard GPU uploads are already zero on these revisits.

The next measured targets are map-local surface/decor preparation, redundant CPU pixel copies and map presentation data
parsing. Some decoded image work remains even when the GPU texture is resident. Complete surface cooking, tighter
CPU/render dependency handoff, and predictive door prefetch can address that. Future dynamically introduced effects,
inventory/house interactions, contextual audio, cold storage, full packaged assets and Android need separate long-run
coverage. No p95/p99 claim or universal zero-stutter guarantee follows from these short desktop checks.

For ongoing attribution, enable `OPENYAMM_MAP_LOAD_TIMING=1` and `logging.hitch_trace=true`. The opt-in
`[LoadingReadiness]` line reports warm-render time, GPU-readback support, uploaded/resident resources and preparation
high-water marks. Ordinary gameplay does not emit new per-asset diagnostic noise.
