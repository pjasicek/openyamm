# Calibration data

See devdocs/map_studio/CALIBRATION.md. `originals/` holds the comparison metrics of the four calibration maps as
shipped (`oymap metrics <map> --world <w> --assets assets_dev --reach`), the numbers a build is compared with.
**Evaluator only:** a builder must not read this folder, the briefs' prose headers or the original maps.

Regenerate after the metrics change:

    for m in "mm8 out02.odm" "mm7 7out02.odm" "mm7 7d06.blv" "mm6 6d16.blv"; do set -- $m
      build/oymap metrics $2 --world $1 --assets ../assets_dev --reach --out calibration/originals/$1_${2%.*}.metrics.json
    done

## Outdoor maps

`oymap compare <original.odm> --world <w> --with <project> --assets assets_dev --out <folder>` is the measure of an
outdoor rebuild (ten parts, 64 regions; the studio's README, "Outdoor projects"). For pictures in the game:

- `outdoor_materials.py <project> --root <scratch root>`: the built map's terrain material file, made with
  `tools/terrain_materials.py` in a small root of its own and copied into the scratch root (never into `assets_dev`).
- `outdoor_ingame.py <project> <world> <original.odm> <shots.yml> <out> --root <scratch root>`: the same views in
  the original and in the rebuild (`shots.yml` from `oymap compare --out`: the twelve worst regions), with
  `ingame_compare.py`'s difference sheets and `pixels.json`.

The scratch sketches of S4 (`output/studio_s4b/ravenshore`, `harmondale`) were corrected from their originals by
the scripts in `output/studio_s4b/gen/` (the grid as spot heights, road beds, cliff joins, rock on steep ground,
houses of the plots, scatter by block): the record of how those files came about.
