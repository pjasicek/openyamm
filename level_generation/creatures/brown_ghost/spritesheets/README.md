# Brown ghost: MM6–MM8-style directional sprites

Rendered from the fitted-hood, matched-bone-material `brown_ghost.blend` using Blender MCP. This is a new brown
sprite family, prefix **bg42**, staged alongside the 3D asset. Original `m242` sprites and active game tables are unchanged.

## View the result

- `preview_front.png`: animation sequences in a compact labeled overview.
- `preview_directions.png`: front, three-quarter, side and rear views, including the mirrored directions.
- `animations_front.gif` and `animations_directions.gif`: playback previews with preserved clip durations.
- `sheets_5view/<animation>.png`: transparent usable sheets, five stored direction rows.
- `sheets_8view/<animation>.png`: transparent sheets with all eight direction rows, including three mirrors.
- `brown_ghost_mm_sprites.zip`: complete render/frame/sheet package with this README and manifests.

Each sheet has **animation frames in columns** and **directions in rows**. Cells are 256×256, with no gutters or
labels. Read `manifest.json` for exact sheet dimensions, frame order, source poses, timings and coordinate conventions.

| Animation | Frames per direction | Duration | Behavior |
| --- | ---: | ---: | --- |
| Standing | 10 | 2.00 s | Loop; omit the duplicate end-of-loop source pose |
| Attack | 16 | 1.25 s | Anticipation, raised hands, stroke and recovery |
| Float | 10 | 1.50 s | Loop |
| Hit | 10 | 0.75 s | Reaction and recovery |
| Death | 12 | 1.75 s | Recoil and collapse |
| Corpse | 1 | Held | One static frame, rather than ten identical copies; preview holds it for 1 s |
| Fidget | 10 | 1.50 s | Gesture and return |

There are **345 actual renders** (69 samples × five views), 552 PNG direction frames after mirroring, and seven
sheets in each layout. Death, corpse and fidget also have five rendered views here; the original m242 descriptors
used a single image direction for those actions.

## Direction, scale and transparency

Directions 0–4 are rendered at 0°, 45°, 90°, 135° and 180° model yaw under fixed camera/studio lighting. They show front,
front three-quarter, side, rear three-quarter and back. Directions 5, 6 and 7 mirror 3, 2 and 1 respectively, matching
the source family's `Mirror5/Mirror6/Mirror7` convention. They are intentionally not independent opposite-side renders.

A single orthographic projection is fitted to the complete sampled animation/view set. Every frame has the same
scale and a world-ground pivot at **(128, 244)** in the 256×256 image, measured from the top-left image edge. Frames
are not individually cropped, centered or scaled. This keeps the character from changing size or jumping during
playback and leaves room for raised hands and the collapsed pose.

`masters_512/` contains 512×512 RGBA renders for the five stored views. `png_256/` contains native-sized RGBA frames
for all eight directions. PNG sheets retain alpha, including antialiased edges. The indexed BMP family in `bmp_256/`
has five views and shares one palette across every clip: index 0 is transparent cyan **(0, 252, 252)**, followed by
255 opaque colors. Its binary transparency mask uses alpha ≥128 as opaque; PNGs retain smoother transparency.
`palette.json` and `palette.gpl` store the palette. No per-frame palette changes or dithering are used.

Names follow the source-style structure: `bg42` + action letter + frame letter + direction. For example,
`bg42aa0.bmp` is attack frame 1/front, `bg42ap4.bmp` is attack frame 16/back, and `bg42sj2.bmp` is standing frame 10/side.
Action letters are `s/a/w/n/d/x/f`; frame letters begin at `a`; directions are numbered 0–7 for PNG and 0–4 for BMP.

## Timing and later integration

The manifest supplies `animation_length_raw` and each `frame_length_raw`: OpenYAMM's legacy sprite-table loader
multiplies raw lengths by 8 ticks, with actor animation running at 128 ticks/s. Integer raw lengths are distributed
across the selected frame count while preserving each clip's total duration. Source sampling follows those times;
non-looping clips include the endpoint and hold its final sprite. GIF delays are rounded cumulatively to 10 ms.

This package is **art ready for registration**, not an installed game replacement or an original-game LOD archive.
The changed frame counts need new frame-table rows; simply overwriting the old m242 images would keep the old frame
counts. Assign noncolliding sprite/group IDs and register the palette/actor bindings in the intended content package.
Use texture stems without the direction suffix with `Center` and `Mirror5/Mirror6/Mirror7`; set `First`/`HasMore`
according to sequence position. To use the supplied directional death/fidget/corpse sets, do not retain the original
single-direction `Image1` flag. Alternatively, explicitly choose front-only frames for those actions.
No sprite IDs or palette IDs have been allocated by this render job. `manifest.json` is an authoring manifest, not
a directly loadable replacement for OpenYAMM's sprite-group YAML tables. Runtime registration and game-world scale
should be checked when integration is requested.

## Reproduce

In the original workspace, execute `../render_sprites_blender.py` through Blender MCP with `__file__` set to that
script's path. It copies the finished character into a named bake scene, leaves the source model file untouched,
and restores the previous active scene afterward. Inspect an existing bake scene before intentionally rebuilding it.
Wait for `status.txt` to say `RENDER COMPLETE`, then run:

```sh
python3 level_generation/creatures/brown_ghost/pack_sprites.py
```

The packer verifies the source-model hash, frame bounds, shared indexed palette, binary transparency and timing.
It builds the sheets, previews and ZIP. Keep the rendered master set and its matching manifest together; do not mix
frames from different model revisions. The 3D model and authoring scripts remain in the parent workspace and are not
duplicated inside the sprite ZIP.
