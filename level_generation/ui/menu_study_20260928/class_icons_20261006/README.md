# Party creation class emblems

Superseded by [the simpler MM6/MM7-inspired icons](../class_icons_simple_20261006/README.md). The old runtime PNGs are preserved in `output/imagegen/class_icons_simple_20261006/previous_emblems/`.

Generated with built-in imagegen on 2026-10-06 for all 16 selectable classes.
The exact submitted prompts and source-image paths are retained in [prompts.json](prompts.json).
Full-resolution transparent masters are retained in `output/imagegen/class_icons_20261006/masters/`.

Runtime images are 128×128 transparent PNGs in `assets_dev/engine/hud_x2/menus/classes/`.
Export command: `convert MASTER.png -resize 128x128 RUNTIME.png`.
Filename stems are normalized class names; the debug Lich preset uses the Necromancer emblem.
The modal displays 28-unit icons, and the selected character displays a 34-unit emblem beside the portrait.

Native captures and a repeatable input tour: `output/screenshots/class_icons_20261006/`.
Validation: all 16 classes have transparent runtime assets; 258 party creation assertions passed.
