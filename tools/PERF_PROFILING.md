# Desktop CPU profiling with perf

Run these commands from the repository root. `build-prof` keeps release optimization and adds debug information
for source locations and sampled call stacks. It does not enable gprof instrumentation.

## Fastest route: where does the frame time go?

For "the FPS dropped" or "mode A is slower than mode B", profile the ordinary `build/game/openyamm`: no profiling
build is needed. The release binary keeps its symbols, and DWARF unwinding works from its `.eh_frame`. About two
minutes end to end:

```sh
# 1. Numbers first. Each run prints its record folder; run.json has the median FPS, measurement.log the per-second
#    [FramePerf] (loop, render callback, bgfx frame), [GameFramePerf] (update, world, HUD) and [GpuFrameResources]
#    (draws, triangles) lines. Run each case twice; single seconds swing by 10 %.
SDL_AUDIODRIVER=dummy ./tools/run_game.sh --isolated case_a --world mm6 --save saves/a.oysav \
  --warmup 5 --seconds 12 --visible

# 2. Profile the same run: start it in the background, attach once it is in gameplay, wait for it to exit.
(SDL_AUDIODRIVER=dummy ./tools/run_game.sh --isolated case_a_prof --world mm6 --save saves/a.oysav \
  --warmup 5 --seconds 13 --visible > /dev/null 2>&1 &)
sleep 14
perf record -F 1500 --call-graph dwarf,16384 -p "$(pgrep -x openyamm | head -1)" -o /tmp/a.data -- sleep 5
sleep 8

# 3. Text, then the summary. Never leave out --no-inline.
perf script -i /tmp/a.data --no-inline -F tid,ip,sym > /tmp/a.txt
tools/perf_stacks.py /tmp/a.txt                                  # threads by share; the busiest one's functions
tools/perf_stacks.py /tmp/a.txt --thread 1 --frame-us 600 --under renderGameplayHudArt
tools/perf_stacks.py /tmp/a.txt --thread 1 --frame-us 600 --children GameplaySoloHud::renderHud
tools/perf_stacks.py /tmp/a.txt --thread 1 --callers tolower
```

Rules that cost an hour when ignored (2026-11-15):

- **`--no-inline` on every `perf script` and `perf report`.** Without it perf resolves inlined frames through
  `addr2line`, one process at 100 % CPU for minutes, and the report looks hung. With it the 230 MB capture above
  converts in under a second. `perf report -g` on this binary is slow even so: use `perf script` and
  `tools/perf_stacks.py`.
- **`--call-graph dwarf`, not `-g`.** The build has no frame pointers, so `-g` stacks end in `[unknown]` after one
  frame. Without call stacks at all (`perf record -F 2000 -p PID`), self time per function still works.
- **Which thread is the limit.** Thread 0 in the tool's list is normally bgfx's render thread (GL driver, uniform
  commits, one entry per draw), thread 1 the main thread. In `[FramePerf]`, `avg_bgfx_frame_us` well above 50 means
  the main thread waits for the render thread: cut draws and uniform work, not game code. A run at half the
  resolution (`--set video.resolution=800x450`) with the same FPS rules out pixel cost.
- **`--frame-us`** turns shares into microseconds of a frame: pass the thread's busy time per frame
  (`avg_render_callback_us` for the main thread).
- **Compare two cases** by running the tool on both captures with the same `--under`; an old binary from `output/`
  can stand in as a baseline through `--binary`, but only with saves and assets it can load.
- **A quiet machine.** Another session compiling in the checkout triples the frame times: check `uptime` and
  `pgrep -x cc1plus` before trusting a run, and repeat it if either shows load.
- Wait for the game by its exact name (`pgrep -x openyamm`), never `pgrep -f`.

The sections below are the longer route: a profiling build with source lines and the gameplay-gated launcher.

## Reusable approval wrapper

Use `./tools/profile_game.sh` as the command-prefix approval, including for future agent runs. It delegates to
the existing profiler and limits targets to executables named `openyamm`; attachment additionally checks ownership.
Sandbox approval persistence is controlled by the client, not by AGENTS.md or this script.

If the kernel blocks sampling, `./tools/profile_game.sh --enable-user-perf` runs only
`sudo -n /usr/sbin/sysctl -w kernel.perf_event_paranoid=2`. This allows own-process userspace profiling until reboot.
It does not run the game as root or install a persistent system setting. If sudo requires authentication, run
`sudo /usr/sbin/sysctl -w kernel.perf_event_paranoid=2` once in a terminal; the wrapper never accepts a password.

For an isolated desktop run, launch with `tools/run_game.sh`, wait for loaded gameplay/warmup, then read the game
PID from its `run.json` and attach:

```sh
./tools/profile_game.sh --pid GAME_PID --warmup 0 --seconds 20 --output /tmp/sorpigal.data
```

Attachment records only that game's threads for the requested duration; it does not freeze simulation or pause
around map changes. Keep the scene loaded. The launch mode below retains automatic gameplay gating.
Check wrapper changes with `python3 tools/test_profile_game.py`.

## Build

```sh
cmake -S . -B build-prof -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  '-DCMAKE_C_FLAGS_RELEASE=-O3 -g -DNDEBUG' \
  '-DCMAKE_CXX_FLAGS_RELEASE=-O3 -g -DNDEBUG' \
  -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
  -DOPENYAMM_ENABLE_GPROF_SAMPLING=OFF \
  -DOPENYAMM_BUILD_TESTS=OFF \
  -DOPENYAMM_BUILD_EDITOR=OFF \
  -DOPENYAMM_BUILD_TOOLS=OFF
cmake --build build-prof --target openyamm -j25
```

The initial local setup copied the existing `build-gprof/_deps/*-src` dependency sources into
`build-prof/_deps/` and configured `FETCHCONTENT_FULLY_DISCONNECTED=ON` to build without downloads.
For a fresh build directory without those sources, leave that option off (the default).
FFmpeg uses the repository's separate configure/build procedure.

## Record New Sorpigal gameplay

```sh
./tools/profile_game.sh -- --world mm6 --map oute3.odm
```

This launches `build-prof/game/openyamm` with ordinary settings/assets/saves and starts perf with counters
**disabled**. Enter/load New Sorpigal if the main menu opens. Collection starts only when the game's gameplay
screen has a loaded map, the outdoor sprite warmup queue is empty, and three additional seconds have elapsed.
Wait for `[Perf] collection enabled`, then play for 60–120 seconds and close the game normally to finish.
Stand still during warmup: the existing sprite warmup queue can defer work while the camera is moving.

Collection pauses before map loading, while the loading overlay or a separate screen is active, and at shutdown.
It resumes after gameplay is ready again, with the same warmup. The game waits for perf to acknowledge each
state change. This excludes map initialization and queued sprite preparation; assets requested later by actual
play remain part of gameplay costs. The existing gprof gate uses the same readiness check, while its headless
map-loading scope remains specific to gprof.

The result is `build-prof/perf-gameplay.data`. The wrapper uses 199 Hz userspace CPU-cycle sampling and DWARF
call stacks with a 16 KiB stack snapshot. It includes the game's threads. No sudo is needed with permissions
configured as below. Normal launches without this wrapper do not activate perf control.

Useful options before `--`:

- `--output build-prof/sorpigal-before.data`: choose a separate capture name.
- `--warmup 10`: wait ten seconds after each return to ready gameplay (`0` starts immediately when ready).
- `--include-loading`: record the entire process, including startup, asset loading, menus and shutdown;
  gameplay gating and warmup are disabled in this mode.

Use the same route, settings, resolution, VSync and warmup when comparing changes. This wrapper runs the
profiling executable directly; `tools/run_game.sh` continues to run the ordinary development executable.

## Inspect or export

```sh
perf report --no-inline -i build-prof/perf-gameplay.data
perf report --stdio --no-inline -i build-prof/perf-gameplay.data \
  > build-prof/perf-gameplay.txt
perf report --stdio --no-inline --no-children --sort comm,pid,dso,symbol \
  -i build-prof/perf-gameplay.data > build-prof/perf-gameplay-threads.txt
```

These reports include sampled call stacks and inclusive costs (a function together with its callees).
The second text report separates threads and shows self costs (`pid` is perf's command/TID sort key).
`--no-inline` avoids addr2line warnings observed on this machine during inline expansion; it does not disable
stack capture. Source/debug information remains in the executable. These are sampled CPU costs, not exact
call counts, elapsed frame times, or GPU execution measurements. Shared-library symbol detail depends on the
symbols available for those libraries. Check the recording output for lost samples or unwinding warnings.

Keep the `.data` file and the matching executable/debug information until analysis is finished; analyze or
archive them before rebuilding. `build-prof/` is ignored by Git. Use different output names for comparisons.

## Prerequisites

On Ubuntu, install `linux-tools-common` and `linux-tools-$(uname -r)`. `perf version --build-options` should
show DWARF/unwind support. If profiling is restricted, `sudo sysctl -w kernel.perf_event_paranoid=2` allows
own-process userspace profiling until reboot. The commands above explicitly select userspace events.

References: [perf record](https://man7.org/linux/man-pages/man1/perf-record.1.html),
[perf permissions](https://www.kernel.org/doc/html/latest/admin-guide/perf-security.html).

## Validation

The optimized profiling build passed. A native perf integration check captured two gameplay intervals with
no loading/warmup samples and zero lost samples; `--include-loading` captured all three phases. The actual
New Sorpigal headless map-loading diagnostic completed in both modes: default gating produced zero CPU samples,
and loading mode produced readable game call stacks. This verifies collection control, not desktop GPU performance.
