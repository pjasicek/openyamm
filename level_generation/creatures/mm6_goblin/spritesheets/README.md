# MM6 goblin directional sprite delivery

Rendered from the packed `../mm6_goblin.blend` identified by SHA-256 in `render_manifest.json`.
All 552 cells are genuine renders of the final rig, including the opposite side of its right-hand sword.

| Action | Frames per direction | Directions | Exact duration | Legacy subset |
| --- | ---: | ---: | ---: | ---: |
| Standing | 10 | 8 | 2 s | 10 frames, 32 raw units |
| Walk | 10 | 8 | 0.75 s | 10 frames, 12 raw units |
| Attack | 16 | 8 | 0.75 s | 12 frames, 12 raw units |
| Hit | 10 | 8 | 0.75 s | 10 frames, 12 raw units |
| Death | 12 | 8 | 0.625 s | 10 frames, 10 raw units |
| Corpse | 1 | 8 | 0.125 s held | 1 frame, 2 raw units |
| Fidget | 10 | 8 | 0.75 s | 10 frames, 12 raw units |

## Files

- `masters_710x578/`: 552 transparent renders at twice the native-size delivery resolution.
- `png_355x289/`: 552 RGBA frames, premultiplied-alpha Lanczos downsampling.
- `bmp_355x289/`: 552 indexed frames sharing one palette; index 0 is transparent cyan `(0,252,252)`.
- `sheets_8view/`: seven usable, transparent, unlabeled atlases. Columns are animation frames; rows are directions 0–7.
  Each cell is 355×289. Ten-column sheets are 3550×2312, attack 5680×2312, death 4260×2312, corpse 355×2312.
- `previews/`: labeled direction strips, animation GIFs, and separate visual review images. These are not usable atlases.
- `manifest.json`: exact source samples, display intervals, camera, pivot and outputs.
- `legacy_manifest.json`: positive integer timings and selected frame stems for prospective native frame groups.
- `palette.json` / `palette.gpl`: shared palette. `validation.json`: image/palette/timing checks.
- `mm6_goblin_mm_sprites.zip`: masters, delivery images, sheets, previews, palettes, manifests and this README.

## Direction, naming and placement

Staged prefix is `rgob`; action letters are `s,w,a,h,d,c,f`, followed by frame letters `a` onward and direction `0`–`7`.
For example `rgobsa0` is Standing frame 0 viewed from the front, `rgobap4` is Attack frame 15 viewed from behind.
Direction 0 is front; 1 is front oblique with nose toward screen right; 2 is that profile; 3 is rear oblique; 4 is back;
5–7 are the real opposite-side views. Actor rotations increase by 45° around Blender Z with fixed lights/camera.
Check your consumer's angular convention when registering groups. Do not apply native Mirror5/6/7 or Image1 flags.

Every frame uses one scale and ground pivot **(177.5,277)** in the 355×289 image, with origin at its top left.
Camera spans 2.6217335 m horizontally / 2.1343126 m vertically; it is about 135.4066 pixels per meter.
This fit includes the sword's full motion and prone corpse. Native front Standing had 256 visible pixels of height;
the generated front Standing bounds are (107,22)–(246,279), or 257 pixels tall. All measured bounds are in
`validation.json`; do not independently stretch poses.

The ground pivot is **12 pixels above the canvas bottom**. Native `gob` frames touch the bottom and omit `Center`.
A future bottom-anchored billboard needs its rendered canvas bottom 12 pixels below actor ground (at this render scale,
about 0.08862 m), or an equivalent explicit pivot/offset in the importer. Account for runtime scale as well.
Setting `Center` is not the correction. No anchor/runtime integration was installed by this generation.

## Timing

Use `manifest.json` for full-quality playback. Every frame has a positive display interval; clip duration is unchanged
except Standing's deliberate extension from a static image to a two-second idle. Loop sampling omits a duplicate last
pose; nonloops include both endpoints. Pose sample times and display intervals are separate: endpoint-inclusive
nonloop samples approximate the continuous movement within its original duration. Use the model clips for exact
continuous interpolation. Hold Corpse after Death. GIF centiseconds round Death to 0.62 s; GIFs are review previews,
not the timing authority.

Legacy timing has 16 raw units per second. Sixteen positive Attack frame lengths cannot fit into the native 12 raw
units, nor can twelve Death frames fit into ten. `legacy_manifest.json` selects 12 and 10 existing rendered samples
respectively, preserving duration with no zero-length frames. It similarly distributes raw units over the other
clips. These are proposed frame-group inputs, not a ready-made live table or allocated IDs. The original three goblin
variants and their palette/scale remaps remain unchanged; this delivery contains one reconstructed base palette.

## Repacking and review

Use `../render_sprites.py` to resume only masters from the same saved model hash. `../pack_sprites.py` packages a
completed render and verifies counts, bounds, transparency, shared palette and timing. Packaging uses alpha ≥128 for
opaque BMP pixels; PNGs retain antialiased alpha. At native size, inspect the indexed contours and color bands beside
the PNGs, as well as all eight view rows across animation. Retain the transparent masters for future repacking.

After visual review, archive with:

```sh
python3 -c "import sys; sys.path.insert(0, 'level_generation/creatures/mm6_goblin'); import pack_sprites; pack_sprites.archive()"
```

Source model, editable rig, selected AI references, exporter and detailed calibration are in the parent project.
See `../DELIVERY_AUDIT.md` for actual final review and validation evidence.


Final review: `previews/png_bmp_native_size.png` compares eight representative poses/views at native dimensions;
`*_contact_*.png` contains labeled pages for every pose and direction. Reviewed contacts preserve sword handedness,
strike extension, distinct hit/fidget motion, foot placement and the prone endpoint. Palette reduction retains the
important material separation. BMP contours are harder than PNG antialiasing by design; the alpha threshold and
cyan index are explicitly verified. Filtered alpha may extend slightly below the nominal ground pivot.
