# Simple party creation class icons

Replaces the earlier decorative emblems with one recognizable object per class, following the original MM6/MM7 party creation icons and the user's request for simpler Obsidian art. Generated with the built-in `image_gen.imagegen` tool on 2026-10-06. Exact generation prompts, the Vampire alpha repair, and original output paths are in [prompts.json](prompts.json).

| Class | Symbol | Original reference |
| --- | --- | --- |
| Knight | Sword | MM6 `6ic_knig` / MM7 `ic_knig` |
| Archer | Bow | MM6 `6ic_arch` |
| Cleric | Ankh | MM6 `6ic_cler` / MM7 `ic_cler` |
| Priest | Holy book | New symbol |
| Druid | Oak tree | MM6 `6ic_druid` / MM7 `ic_druid` |
| Monk | Yin-yang | MM7 `ic_monk` |
| Paladin | Plain blue shield | MM6 `6ic_palad` / MM7 `ic_palad`, without the heraldic horse |
| Ranger | Traveling boots | MM7 `ic_ranger` |
| Thief | Dagger | MM7 `ic_thief` |
| Sorcerer | Gold/red magic star | MM6 `6ic_sorc` / MM7 `ic_sorc` |
| Necromancer | Bare skull | New symbol |
| Vampire | Bat | New symbol |
| Dark Elf | Pointed-ear profile | New symbol |
| Minotaur | Bull head | New symbol |
| Troll | Wooden club | New symbol |
| Dragon | Dragon head | New symbol |

Original archive members were verified in `reference/mmerge_datapatch/Data/mm6.icons.lod` and `mm7.icons.lod`. The extracted originals are under `assets_legacy/icons_20260926/worlds/mm6/icons/6ic_*.bmp` and `assets_legacy/icons_20260926/engine/icons/ic_*.bmp`. Reference sheets, copied originals and source provenance are in `output/imagegen/class_icons_simple_20261006/reference/`.

Runtime images: `assets_dev/engine/hud_x2/menus/classes/`, all 16 lowercase 128×128 RGBA PNGs, mode 0644. Full-resolution masters: `output/imagegen/class_icons_simple_20261006/masters/`. Previous runtime emblems: `output/imagegen/class_icons_simple_20261006/previous_emblems/`. The first Vampire result is retained as `masters/vampire-before-alpha-repair.png`.

Export: `convert MASTER.png -resize 128x128 RUNTIME.png`. Checked dimensions, alpha range 0–255 and transparent corners for every runtime icon. The same cached textures and drawing paths are used: 28 logical units in each class button and 34 beside the selected portrait; no renderer or layout changes.

Menu-size contact sheet: `output/imagegen/class_icons_simple_20261006/icons-at-menu-size.png`. Repeatable native capture tour: `output/screenshots/class_icons_simple_20261006/tour.yml`.

Native validation completed on OpenGL 3.3/NVIDIA under Wayland: all 13 screenshots captured, covering the Human grid and Vampire, Dark Elf, Minotaur, Troll and Dragon class grids and selected portraits. Exit 0; no class texture errors. Run record and log are retained beside the screenshots.
