# Obsidian area-transition loading window — native, 2026-09-29

Replaces the old `bardata` / `ia02-*` loading overlay with the accepted Obsidian modal artwork,
the rest screen's stable glass shell and conserved sand animation, and a code-drawn red progress bar.

The final user refinement makes the panel **300 × 112 logical pixels**, with a **32 × 48 hourglass**.
The width matches the old loading window's 300 logical pixels. The hourglass runs at **4× rest speed**:
two seconds of sand flow, then a quarter-second turn, repeating in the other orientation. Its full cycle
is 4.5 seconds. The rest screen retains its existing timing and dimensions.

[Native visual review](index.html) · [Loading screenshot](native/loading-12.png) ·
[Mounted layout](../../../assets_dev/engine/ui/gameplay/loading.yml)

## Integration

- `game/ui/screens/LoadingOverlayScreen.*` owns the transition presentation and its independent clock.
- `assets_dev/engine/ui/gameplay/loading.yml` owns positions, dimensions, artwork and the Fondamento title.
- `game/ui/RestHourglassAnimation.h` remains the shared animation source. No additional atlas is generated.
- `MenuScreenBase::drawTextureRegionColor` accepts optional rotation about the destination centre.
  Both sand and shell rotate about the same centre, preserving the approved sand volume and silhouette.
- The concurrent loading-background work retains the outgoing world/dialogue under the window.
- Illustrated full-screen loading pages retain their existing artwork and progress presentation.

The separate [approved cleanup](../obsolete_ui_cleanup_20260929/README.md) removed 528 obsolete runtime files.
Old `bardata` and `ia02-*` exports were not part of that reviewed batch; their legacy `turnhour` registration
is still present in `icon_frame_data.txt` and requires an explicit retirement before removing those files.

## Checks

The desktop build passes. Existing Obsidian unit coverage passes (17 cases, 2,436 assertions), including
hourglass frame bounds, the conserved sand cycle and seamless orientation changes. Deployment verification
passes for all 9,430 active accepted icons, with 490 retired exports excluded.

Native OpenGL/Wayland screenshots on the NVIDIA GPU show New Sorpigal's Abandoned Temple entrance, the small
window during loading, and arrival in `6d02.blv`. The red bar, title and smaller hourglass fit within the
frame. The hourglass's entire rotated rectangle remains clear of the panel edges and text column.
This is desktop MM6 visual coverage; it is not an Android-device check.

The [run receipt](native/run.json) records the capture executable and isolated settings. The review used
[a temporary capture probe](capture-probe.patch) to invoke entrance event 102 and hold one loading step long
enough to capture four native frames. It changed only review timing, not the window rendering, and was removed
before the final production rebuild. The receipt's timing/FPS therefore does not measure normal map-loading
performance. [tour.yml](tour.yml) contains the confirmation/capture steps used with that probe.
