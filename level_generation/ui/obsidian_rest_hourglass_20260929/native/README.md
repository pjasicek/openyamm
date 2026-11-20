# Native rest hourglass

Integrated on 2026-09-29 after the user approved the painted design and the 2140 quantity correction.
[Native capture gallery](index.html). The shared rest renderer/layout covers desktop and Android, indoors and outdoors.

## Runtime

- `assets_dev/engine/icons_x2/obsidian_rest_hourglass_frame.png`: one 256 × 384 RGBA shell, including translucent glass.
- `obsidian_rest_hourglass_sand.png`: a 1216 × 2312 RGBA atlas with 129 conserved fill states per orientation. Each
  sand crop is 72 × 132 pixels at the standard 2× logical resolution, surrounded by two transparent gutter pixels.
- The two native quads share a pivot. Sand is drawn beneath the glass, with an eight-second drain and a one-second
  eased half-turn. Completed orientations persist; both orientations make an eighteen-second complete loop.
- Fill geometry is baked from the approved `sand-volume.mjs` and SVG composition. There is no second C++ volume
  model to diverge from it. The native turn runs every rendered frame; the static shell is never regenerated.
- At each loop boundary the next upper reservoir uses the exact rotated texels of the previous full lower pile.
  This avoids a small difference between separate SVG clip rasterizations of the same endpoint.
- The textures load on first opening Rest. Base RGBA data totals 11.1 MiB, with ordinary UI mipmaps and caches in
  addition; compressed PNGs total about 918 KiB. The game draws two textured quads per hourglass frame.

`game/ui/RestHourglassAnimation.h` maps the existing elapsed timer to the sand cell and continuous rotations.
`RestHourglassAtlas.h` is generated atlas/timing metadata. `GameplayPartyOverlayRenderer.cpp` owns the shared drawing;
`GameplayUiRuntime::submitHudTexturedQuad` accepts an optional rotation around the quad centre. Existing callers retain
their default zero rotation. `GameplayScreenController` wraps the timer over eighteen seconds to retain precision.

`assets_dev/engine/ui/gameplay/rest.yml` reserves the approved 72 × 108 logical rectangle at `(384,161)`. The date block
is `(364,151,248,133)`, with a fine divider, date text to the right and Exit Rest centred underneath.
The subsequent width refinement removes twelve logical pixels (about 10%) from the hourglass section, shifting its
centre left by six and the date text left by twelve. The illustration retains its size and full turning clearance.
Rest/wait action targets, their time progression, food cost, live sky and recreated reading fonts retain their behavior.

## Regeneration

From the repository root:

```sh
node level_generation/ui/obsidian_rest_hourglass_20260929/check_sand_volume.mjs
node level_generation/ui/obsidian_rest_hourglass_20260929/export_runtime.mjs
cmake --build build --target openyamm -j25
```

The exporter uses headless Chrome to rasterize the approved SVG, assembles the atlas, installs both PNGs and emits the
C++ metadata. The original generated source PNGs remain unchanged. [export.json](export.json) records dimensions,
hashes, memory and transparent-gutter checks; [atlas_checks.json](atlas_checks.json) records the exact seam comparison.

## Verification

- Development `openyamm` build passed. The concurrent indoor movement compile error encountered during the first
  build was corrected by its ongoing work before the successful rebuild; no movement changes belong to this task.
- Focused `*Obsidian*` unit suite: **16 cases / 2,431 assertions passed**, including drain/turn timing, retained
  orientation, periodicity, atlas frame bounds and matching rotation pivots.
- The source volume check passed at 2,010 samples in both orientations; maximum total error is 0.00323%.
- Both exported seam pairs are byte-identical after the half-turn, including alpha. Every crop clears its gutter.
- Native MM6 runs at **1600 × 900** and **1280 × 960** used **OpenGL 3.3 on NVIDIA, SDL Wayland**. Captures cover
  draining, both orientations, turn clearance, one-hour and five-minute waits, Exit Rest and Escape. The clock
  advances by exactly one hour and then five minutes for those actions. Isolated saves preserve normal user saves.
- The shared Android implementation is updated; no APK/device validation or release ZIP repack was performed.

The approved artwork and quantity rule are the production baseline. Do not re-enable the legacy `hglas` sequence or
replace the fixed shell with independently generated animation frames.
