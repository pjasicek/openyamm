# Desktop game runs

`./tools/run_game.sh [game arguments...]` launches the normal `build/game/openyamm` from the repository root,
using the current desktop display and normal settings/saves. It does not rebuild the executable or force a renderer.

## Isolated, repeatable runs

```sh
./tools/run_game.sh --isolated sorpigal_grass_on \
  --world mm6 --map oute3.odm \
  --position -9728 -11319 161 --yaw-radians 4.758 --pitch-degrees -6.274 \
  --set video.terrain_decorations=true --set video.vsync=false \
  --warmup 3 --seconds 15
```

`--isolated --help` lists the options. Map arguments are asset filenames, not display names; `oute3.odm` is
New Sorpigal. Position is in world units, yaw is in radians, and pitch is in degrees, matching the named fields
in the console's `loc` output. Supply all three camera options together. Without them, retain the map/save camera.
The normal movement system still resolves floors and collision; an invalid/below-ground position can be adjusted.

Use `--binary build-vulkan/game/openyamm` to test a separate build. The selected executable performs both
headless preparation and the desktop run; the default remains `build/game/openyamm`.

Every invocation creates a unique `/tmp/openyamm-desktop-<name>-.../` directory and prints its path. It contains:

- `prepare.yml` and `prepare.log`: the faithful headless scenario used to establish the map, party, and camera.
- `saves/startup.oysav`: the resulting private save loaded directly by the graphical game, bypassing the main menu.
- `launch-settings.ini`: the immutable requested settings snapshot; `settings.ini` is the game's writable copy.
- `game.log` and `measurement.log`: full output and the interval after warmup, respectively.
- `renderer-info.txt`: desktop OpenGL renderer information when `glxinfo` is installed.
- `run.json`: requested options, loaded map/camera, binary/settings/save hashes, duration, FPS samples, exit status and errors.

Startup and warmup are excluded from the requested duration. After that duration the wrapper requests normal shutdown
with SIGTERM, waits up to ten seconds, and kills only its own child if necessary. Ctrl+C also cleans up that child.
`--seconds 0` keeps the game open until it is closed. Preparation/startup each have a three-minute timeout.
`--prepare-only` creates the setup without opening a window. Failed save loads stop instead of starting a different game.
All runs retain their records for review; delete their temporary directories when no longer needed.

For a one-shot resource and per-view GPU timing diagnostic, add
`--set debug.effect_stats_delay_seconds=12`. This opts into bgfx GPU timestamp queries and writes
`[GpuViewPerf]` entries with view names and microseconds. Leave it unset for ordinary FPS comparisons;
the extra timing queries themselves have a cost.

Optional screen-space ambient occlusion is under Settings → Video → Colour & effects. For an isolated run,
use `--set video.ambient_occlusion=true` and optionally `--set video.ambient_occlusion_strength=35` (0–100).
It defaults to disabled; disabling it or setting strength to zero removes its render targets and GPU passes.
It works independently of cinematic grading and applies to opaque world geometry and 3D models.

## Native screenshots and YAML tours

The normal `main` build includes engine-native PNG capture through bgfx's screenshot callback.
It captures the game and HUD without desktop screenshot utilities or Xvfb, including on Wayland.
Rebuild with `cmake --build build --target openyamm -j25` after pulling the capture implementation.

In the debug console, `screenshot coast` saves `output/screenshots/coast.png` relative to the game's
working directory. Names allow letters, digits, underscores and hyphens; existing named images are overwritten.
The command closes the console before capture so its text does not cover the screenshot.

## Menu checks with isolated saves

`--menu` starts the isolated game at its title screen. Without `--map` or `--save`, it starts with an empty private
save directory and skips headless map preparation. Combining `--menu` with either option prepares a private save
for Continue/Load checks while still opening the title screen.

`--set debug.menu_input_tour_path=/absolute/menu-tour.yml` replays menu input through the native input frame and
screen event handlers, including under Wayland. It is a one-shot launch setting and is never written back to the INI.

```yaml
output_dir: ../captures
exit: true
steps:
  - capture: main-menu
  - key: Tab
  - key: Return
  - wait: 1
  - capture: next-screen
```

Supported steps are `click: [x, y]` in the menu's 1600×900 design coordinates, `key: Escape` using an SDL scancode
name, `text: My party`, `wheel: -3`, `wait: 1.5` in seconds, and `capture: name` for a PNG. Clicks scale with the
centred menu canvas. Text requires an active SDL text-input session and travels through the SDL event queue to the
currently active field. `pointer_down`, `pointer_move` and `pointer_up` accept the same coordinate pair for dragging;
`key_down` and `key_up` hold and release a key across frames. `expect: gameplay`, `expect: pause`,
`expect: text_input` and `expect: menu_cursor` fail the run when their screen/input condition is not met.
The cursor check verifies visibility and disabled relative mode on the game window, independently of desktop focus.
For gameplay checks, `action: quest` (or another keyboard binding INI key) presses the native gameplay action.
`right_down: [x, y]` and `right_up: [x, y]` hold/release RMB for inspectors and modern cursor interaction.
These operations use the same input frame as the real controls; they do not invoke UI renderer callbacks.
For repeatable camera-rotation profiling in modern controls, `look_rate: [-400, 0]` supplies relative mouse
motion in pixels per second during subsequent `wait` steps. `look_rate: [0, 0]` stops it. This uses ordinary
gameplay mouse-look and leaves simulation running; begin after loading and any screenshot pose tour finishes.
For walking, `action_down: forward`, followed by a `wait` and `action_up: forward`,
holds and releases the configured gameplay action. Use these action steps for sustained gameplay input;
raw `key_down`/`key_up` steps deliver screen keys after gameplay actions have already been resolved.
With gameplay active, raw key steps enter the ordinary SDL event path, including the debug console. Use
the backquote key, `text: "model pause 0"`, `key: Return`, and the backquote key again to issue a console command
and close the console before a capture.

The tour waits for frame readback before exiting;
`exit: false` returns control to normal input. Relative output directories resolve against the tour's directory.
The [native menu integration](../level_generation/ui/menu_study_20260928/NATIVE_INTEGRATION.md) includes checked-in tours.

## Gameplay screenshot tours

For a delayed single capture, add these options to an isolated launch:

```sh
--set debug.screenshot_path=/tmp/openyamm-coast.png \
--set debug.screenshot_delay_seconds=4
```

The delay starts when gameplay is available and the loading overlay has closed. It must be between
0 and 600 seconds. Allow enough launch time for loading, the delay and frame readback. Ordinary movement
and gravity still apply to single captures; use a tour for exact elevated viewpoints.

A YAML tour applies multiple poses in the current map, captures them in order, and optionally exits:

```yaml
output_dir: ./captures
settle_seconds: 1.5
exit: true
shots:
  - name: coastline
    position: [1370.718, -8612.107, 974.502]
    yaw: 0.322
    pitch: -0.3714933313
  - name: offshore
    position: [1370.718, -8612.107, 974.502]
    yaw: 0.7
    pitch: -0.3714933313
    settle_seconds: 2
```

`position` uses native party-foot coordinates, matching `loc`; yaw and pitch are **radians**.
Outdoor heights are applied exactly, including airborne poses, without a Fly buff or floor snapping.
Gameplay simulation is held during the tour so gravity, movement and combat cannot move the viewpoint.
Rendering continues during settling. Normal gameplay resumes after a tour with `exit: false`.
Indoor placement uses the ordinary indoor position resolver. Tours do not switch maps or worlds.

`output_dir` defaults to `output/screenshots/tour`; relative directories are resolved against the YAML
file's directory, not the isolated run directory. PNG names are `01-coastline.png`, `02-offshore.png`, etc.
Each shot can override the default settling time (0–600 seconds); even zero allows at least 100 ms for
the new pose to render. Capture errors stop the tour. Logs record requested poses and capture results.

Example: capture New Sorpigal's two checked-in water viewpoints:

```sh
./tools/run_game.sh --isolated water-mm6 --world mm6 --map oute3.odm \
  --warmup 0 --seconds 30 \
  --set debug.screenshot_tour_path="$PWD/tools/screenshot_tours/mm6_water.yml"
```

For Emerald Island use `--world mm7 --map 7out01.odm` and `mm7_water.yml`; for Ravenshore use
`--world mm8 --map out02.odm` and `mm8_water.yml`. These examples write into the repository's
`output/screenshots/water_review/mm6`, `mm7` and `mm8` directories. `exit: true` closes the game as soon
as all images have been written; the launcher's `--seconds` remains an upper time limit after loading.

Video → Water → **Reflect nearby objects** optionally includes creatures, trees and decorations in scenery
reflections. It defaults to off and can be overridden with `--set video.water_sprite_reflections=true`.
It uses the selected reflection detail (512 by default), fades sprites between 3,072 and 4,096 units, and draws
at most 64 sprites per water plane (indoors: 32 decorations and 32 creatures). It shares the existing reflection
textures and animation refresh schedule; particles, projectiles and gameplay labels are excluded.

The three `[debug]` keys `screenshot_path`, `screenshot_delay_seconds` and `screenshot_tour_path` are
launch-only directives. Saving settings deliberately omits them so later launches do not repeat a capture.
Use tours in isolated runs: their poses move the active party, and they are visual diagnostics, not gameplay
or GPU-performance measurements.

## Model and named-effect diagnostics

`./tools/run_sorpigal_demon_crowd.sh` runs a 1600×900 New Sorpigal FPS test with every goblin and
mage/magician presented as the animated demon. It preserves normal rendering settings and actor gameplay
data, using the launch-only `debug.actor_models_manifest=worlds/mm6/models/sorpigal_demon_crowd.yml` override.
Add `--seconds 0` to keep the isolated game open; the default measures 30 seconds after ten seconds of warmup.
The [fixed 229-actor report](../output/performance/sorpigal_demon_crowd_fix_20261005/REPORT.md) retains
matching sprite/model measurements, native captures and CPU attribution.

Shared rigid models and named effects can be spawned during an isolated run without editing map events. These
`[debug]` values are also launch-only and are never written back to the settings file:

```sh
--set debug.model_spawn_path=engine/models/fixtures/shared_model_fixture.glb \
--set debug.model_spawn_clip=bob_spin \
--set debug.model_spawn_x=25269 --set debug.model_spawn_y=-6710 --set debug.model_spawn_z=1450 \
--set debug.model_spawn_scale=160 --set debug.model_spawn_yaw_radians=0.4 \
--set debug.model_spawn_markers=true
```

The model path is package-relative. The clip is optional and loops when supplied. Position uses OpenYAMM world
coordinates; scale must be positive and yaw is in radians. Node markers render local RGB axes for every node,
including empty attachment nodes.

```sh
--set debug.effect_spawn_id=mm9:column_of_fire \
--set debug.effect_spawn_x=25269 --set debug.effect_spawn_y=-6710 --set debug.effect_spawn_z=1413 \
--set debug.effect_spawn_scale=1 --set debug.effect_spawn_yaw_radians=0 \
--set debug.effect_spawn_count=8 --set debug.effect_stats_delay_seconds=0.75
```

The named MM9-derived effect library is engine-owned and available in every active world. `effect_spawn_count` accepts
1–256 instances and gives each a deterministic seed. A non-negative `effect_stats_delay_seconds` (maximum 600) emits one
peak snapshot containing effect/component counts, draw submissions, texture switches, estimated texture and
transient memory, world-space quad area, and the current bgfx frame counters. Use the same map, camera, resolution,
VSync setting, warmup and delay for A/B measurements. Short-lived effects can expire before the launcher's ordinary
measurement interval, so interpret the delayed snapshot and the first active `FramePerf` sample together.

The debug console exposes the same live services. Run `model list` or `effect list` for indices; `help model` and
`help effect` show spawn, orbit, marker, clip, pause, scrub, replay, update-rate, statistics and stop forms.

To replace a projectile recipe's impact presentation for a live test, open the debug console with the grave key and
run, for example:

```text
effect impact-rebind implosion mm9:column_of_fire
```

The override changes visuals and effect audio only; damage and other gameplay behavior are unchanged. Query it with
`effect impact-rebind implosion`, list all active overrides with `effect impact-rebind`, and restore the normal impact
with `effect impact-rebind implosion off`. Overrides are scoped to the current map runtime and clear on a map reload.

## Existing saves and enhanced assets

```sh
./tools/run_game.sh --isolated sorpigal_saved_view \
  --world mm6 \
  --settings /tmp/openyamm-sorpigal-ground-cover/settings.ini \
  --save level_generation/terrain/mm6_new_sorpigal_dirt_fidelity/references/Dirt_View.oysav \
  --map oute3.odm --position -9728 -11319 161 --yaw-radians 4.758 --pitch-degrees -6.274 \
  --set video.terrain_decorations=false --warmup 3 --seconds 15
```

`--save` is copied before preparation; the original is never the active save. Omit `--map` to keep the saved map.
With no map or camera override, the private startup save is an unchanged copy of the source, preserving its camera
and runtime state without a headless load/save round trip.
With a camera override, the scenario changes maps only if necessary; `--map` without a camera explicitly loads that map.
Without a save, the existing faithful new-game workflow supplies the normal initial party/state.

`--settings PATH` copies a different INI, including its asset scale and rendering preferences. Relative asset roots
are resolved relative to that source INI's directory. `--assets PATH` explicitly selects an asset root.
Repeat `--set SECTION.KEY=VALUE` for rendering/debug settings. The wrapper owns startup controls, asset resolution,
and trace destinations to keep settings, saves and logs isolated; those cannot be redirected by `--set`.
It enables FPS/performance logging, but preserves other settings, including VSync and resolution, unless overridden.
Assets are shared for reading, not duplicated. Startup scripts/simulation still run normally; this is not a frozen scene.

For A/B comparisons, use the same save, pose, asset root, resolution, logging and warmup, changing only the intended
setting. Keep the window focused, avoid input during measurement, and verify the renderer and loaded scene.
The first/last per-second FPS samples may overlap the interval boundaries. These logs are frame-rate observations,
not GPU timer measurements or CPU/GPU attribution. Detailed profiling tools remain separate work.

The engine setting behind direct save startup is `[startup] save_file=...`, used only when
`start_in_main_menu=false`. Empty `save_file` retains ordinary new-session startup. To rebuild after changing it:

```sh
cmake --build build --target openyamm -j25
```

Agents should use the existing `./tools/run_game.sh` approval prefix when desktop access requires escalation.
This wrapper runs the selected game executable and its setup workflow; it does not accept arbitrary shell or
profiler commands and does not configure system profiling permissions.

Validation: normal desktop build and startup-settings round-trip test passed. Fresh-map and copied-save launches
were run on the RTX 3060 Ti and closed automatically with exit code 0. The copied-save run recorded the requested
`(-9728, -11319, 161)` position, yaw equivalent to `4.758` radians (the engine may normalize it negative), and
`-6.274` degree pitch. Main settings, existing user saves and the reference save retained their original hashes.
A missing input save produced a failed run record without opening a game window.
