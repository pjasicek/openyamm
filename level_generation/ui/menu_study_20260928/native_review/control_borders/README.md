# Complete save-row and text-field borders

The 29 September 2026 correction restores the approved thin brass borders around normal/selected save rows and the
shared text field. The mounted PNGs are `omenu_save_row.png`, `omenu_save_row_selected.png` and `omenu_text_field.png`
under `assets_dev/engine/hud_x2/menus/`. The text-field correction also applies wherever that menu skin is reused.

The exporter rounded the screenshot origin down but calculated its size independently, excluding the bottom pixel
when the element started at a fractional Y coordinate. Browser capture also hid the scrollbar and expanded
percentage-width save rows beyond the measured capture rectangle, excluding their right border.
`stage_runtime.mjs` now rounds the two outer endpoints and freezes the measured element dimensions before capture.
The approved CSS, native layouts, border colours and control dimensions are unchanged.

[Corrected exports](exports.json) record the measured rectangles, capture bounds, source hashes and installed hashes.
The three PNGs in [assets/](assets/) are exact copies of the mounted files. The original `runtime_stage/` handoff is
preserved as historical evidence; [native_assets.json](../../native_assets.json) points to these replacements.

Re-export the approved browser surfaces into a separate directory:

```sh
node --check level_generation/ui/menu_study_20260928/stage_runtime.mjs
node level_generation/ui/menu_study_20260928/stage_runtime.mjs --output /tmp/openyamm-menu-border-export
```

Only the three named surfaces were installed for this correction. The export regenerates the full surface collection
for inspection; it does not install runtime assets or alter the frozen handoff when `--output` is supplied.

Pixel checks verify every pixel on all four borders of each corrected surface. Native checks use the ordinary desktop
game on NVIDIA/OpenGL with private saves/settings and engine screenshot readback. The two tours cover new-save and
existing-save selection, active name editing and Load Game at 1600×900 and 1280×720.

- [1600×900 Save Game](captures-1600/save-new.png)
- [1280×720 Save Game](captures-1280/save-new.png)
- [Native and asset validation](validation.json)

```sh
./tools/run_game.sh --isolated menu-borders-1600 --world mm6 --map oute3.odm --warmup 0 --seconds 35 \
  --set video.window_mode=windowed --set video.resolution=1600x900 \
  --set debug.menu_input_tour_path="$PWD/level_generation/ui/menu_study_20260928/native_review/control_borders/save-fields-1600.yml"
```

For the smaller capture, use `video.resolution=1280x720` and `save-fields-1280.yml`.
This is an asset/export correction; it does not require a C++ rebuild.
