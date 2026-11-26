# Game runs, captures and profiling

Moved from the root `AGENTS.md` (section "Native Game Visual Checks") on 2026-11-24, unchanged. Read it before
launching the game, capturing screenshots, waiting on a run or profiling.

- Use `./tools/run_game.sh [game arguments...]` to launch the normal `build/game/openyamm` on the current desktop
  display for real-GPU checks. It runs from the repository root, uses the ordinary settings/assets/saves, and forwards
  arguments directly to the game. It does not build, use Xvfb, or force a renderer; verify the active GPU in the logs.
- For repeatable desktop runs, prefer `./tools/run_game.sh --isolated <name> --world mm6 --map oute3.odm ...`.
  See [Desktop game runs](../../tools/RUN_GAME.md) or `./tools/run_game.sh --isolated --help` for copied settings/saves,
  camera overrides, rendering settings and timed exit. Runs bypass the menu, retain records in a unique temporary
  directory, and close their own game process automatically (default: three-second warmup plus fifteen seconds).
- Agent game runs start minimized so they do not cover the user's desktop: `./tools/run_game.sh` sets
  `OPENYAMM_START_MINIMIZED=1` for plain and `--isolated` runs. The minimized game still renders at full size, so
  engine screenshots, tours, logs and timed exit behave as usual; it never has input focus, so mouse look stays off.
  Pass `--visible` (first argument for plain runs, any position for `--isolated`) only for FPS/performance
  measurements, which a minimized window does not reproduce, or when the user asks to watch. `tools/profile_game.sh`
  always shows the window. Launch the game binary directly only when no wrapper fits, with the same variable.
- The user authorized this desktop launcher. When desktop access requires `require_escalated`, use the saved
  `./tools/run_game.sh` command-prefix approval when available, without asking again. Approval persistence is controlled
  by the client. This approval covers launching the game, not arbitrary profiler commands or system configuration.
- Use `./tools/capture_gameplay.sh <name> --world mm6 --map oute3.odm --stage <stage> ...` for isolated
  Xvfb screenshots and scripted input; `--help` lists save, pose, action and output options. It requires `xvfb-run`,
  which is absent on some hosts; when only scripted stills are needed, prefer the engine-native capture below.
- The user authorized this reusable capture workflow. Use the saved `./tools/capture_gameplay.sh` command-prefix
  approval when available; do not ask again for each camera or run. If the sandbox blocks display sockets, run the
  wrapper with `require_escalated` and that prefix. Approval persistence is controlled by the client, not this file.
- Prefer engine-native screenshot capture over desktop/X11 screenshot tools; the game writes the PNG itself through its
  bgfx frame readback, so it is compositor-independent (Wayland-safe) and includes the HUD. Use absolute output paths
  because isolated runs use their own working directory.
  - One pose: `./tools/run_game.sh --isolated <name> --world mm6 --map oute3.odm --position X Y Z --yaw-radians Y
    --pitch-degrees P --warmup 5 --seconds 12 --set debug.screenshot_path=/absolute/shot.png
    --set debug.screenshot_delay_seconds=4`. The delay counts from gameplay start (map loaded, loading overlay closed);
    give it room while tuning settings.
  - Many poses in one boot: author a tour YAML with `output_dir`, optional `settle_seconds` (default 1.5) and
    `exit: true`, plus `shots:` entries of `name`, `position: [x, y, z]`, `yaw` and `pitch` in radians
    (see `output/test_tour.yml` for an example). Pass `--set debug.screenshot_tour_path=/absolute/tour.yml`; shots are
    written as `NN-<name>.png` in order, and `exit: true` closes the game after the last shot.
  - Interactive: `> screenshot [name]` in the debug console saves `output/screenshots/<name>.png`.
  The `[debug]` capture keys (`screenshot_path`, `screenshot_delay_seconds`, `screenshot_tour_path`, and `time_scale`
  for slow motion) are one-shot launch directives: parsed from the INI but never written back on save, so they fire
  only for the launch that requested them.
- Captures use isolated saves/settings and do not establish real-hardware GPU performance. Inspect the images and logs.
- Game runs may overlap: several agents' runs and the user's game can be up at once, so do not wait for another game
  to close before launching. Use `--isolated` with a unique name so runs do not share settings or saves. Only
  performance measurements and investigations need a single session, and the user arranges those.
- When waiting for your own game run or helper script, wait on its exact PID (`kill -0 <pid>`). Never wait on
  `pgrep -f <text>`: your own `bash -c` command line, heredoc or launcher
  contains that text, so the wait matches itself and never ends. Run one sequential queue script rather than chained
  background waiters.
- For anything drawn on the gameplay HUD or the fullscreen gameplay screens, follow
  [HUD rendering](../../devdocs/HUD_RENDERING.md): draw only through the HUD functions (they fill one draw list that is
  drawn once per frame, in call order); read game state when drawing and keep no "changed" flags; a number that
  needs a walk over actors or bags goes through `HudReading`; group fills, frames and text lines of a row into one
  call. Check a change with `avg_hud_draws` in the run log and the `[HudDraw]` listing.
- For "the FPS dropped" or "this mode is slower" questions, start with the fastest route in the
  [perf workflow](../../tools/PERF_PROFILING.md#fastest-route-where-does-the-frame-time-go): two visible isolated runs for
  the numbers (`[FramePerf]`, `[GameFramePerf]`, draws), then `perf record --call-graph dwarf` on the ordinary build,
  `perf script --no-inline -F tid,ip,sym` and `tools/perf_stacks.py` (per thread: inclusive time, callees, callers).
  Always pass `--no-inline`; never use `perf report -g` on this binary (addr2line runs for minutes at full CPU).
- For CPU profiling, use `./tools/profile_game.sh` with its saved command-prefix approval; the user authorized
  this reusable OpenYAMM profiling wrapper. `--enable-user-perf` sets `perf_event_paranoid=2` until reboot when
  needed; administrator authentication is separate from sandbox approval. See [perf workflow](../../tools/PERF_PROFILING.md).
  Do not request broader shell/Python permissions or run the game as root.
